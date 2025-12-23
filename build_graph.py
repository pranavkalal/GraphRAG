import os
import glob
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_openai import ChatOpenAI
from langchain_text_splitters import MarkdownHeaderTextSplitter

from parse_docs import DocumentParser
from kg_extract import KGExtractor

load_dotenv()

class KnowledgeGraphBuilder:
    def __init__(self):
        # Neo4j Connection
        uri = "bolt://localhost:7687"
        user = "neo4j"
        password = os.getenv("NEO4J_PASSWORD", "cotton-crdc-pw")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # Components
        self.parser = DocumentParser()
        
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)  # Use mini for prototyping (cheaper)
        self.extractor = KGExtractor(llm)

    def close(self):
        self.driver.close()

    def add_triples(self, triples, source_file):
        """
        Ingests a list of CRDCTriple objects into Neo4j with typed nodes and relationships.
        """
        with self.driver.session() as session:
            for triple in triples:
                session.execute_write(self._create_triple, triple, source_file)

    @staticmethod
    def _create_triple(tx, triple, source_file):
        # Use dynamic labels based on entity type
        # Fall back to 'Entity' if type is not provided
        subject_label = getattr(triple, 'subject_type', 'Entity') or 'Entity'
        object_label = getattr(triple, 'object_type', 'Entity') or 'Entity'
        rel_type = triple.relationship.upper().replace(' ', '_')
        
        # Cypher query with dynamic labels using APOC or parameterized approach
        query = f"""
        MERGE (s:{subject_label} {{name: $subject}})
        MERGE (o:{object_label} {{name: $object}})
        MERGE (s)-[r:{rel_type} {{source: $source}}]->(o)
        """
        tx.run(query, 
               subject=triple.subject, 
               object=triple.object, 
               source=source_file)

    def process_directory(self, data_dir):
        # Process specific files for the pilot (under 7MB for Azure)
        target_files = [
            "CRDC Charter of Corporate Governance 2024.pdf",
            "CRDC Performance Report 2024-25.pdf",  # 5.3MB - Investments & projects
            "CRDC Project List 2025-26.pdf",  # 410KB - All funded projects
            "CRDC AOP 2025-26 summary.pdf",  # 445KB - Annual plan
        ]
        
        files = [os.path.join(data_dir, f) for f in target_files]
        print(f"Processing {len(files)} files for Knowledge Graph pilot...")
        
        for file_path in files:
            filename = os.path.basename(file_path)
            print(f"\nProcessing {filename}...")
            
            try:
                # 1. Parse
                markdown_content = self.parser.parse_pdf(file_path)
                if not markdown_content:
                    print(f"Skipping {filename}: No content parsed.")
                    continue
                
                # 2. Chunk (Structure-Aware)
                headers_to_split_on = [
                    ("#", "Header 1"),
                    ("##", "Header 2"),
                    ("###", "Header 3"),
                ]
                splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
                chunks = splitter.split_text(markdown_content)
                print(f"  Split into {len(chunks)} chunks.")
                
                # 3. Extract & Ingest
                total_triples = 0
                for i, chunk in enumerate(chunks):
                    text = chunk.page_content
                    # Include header context in the text for the LLM
                    if chunk.metadata:
                        header_context = " > ".join(chunk.metadata.values())
                        text = f"Context: {header_context}\n\n{text}"
                    
                    triples = self.extractor.extract_triples(text)
                    if triples:
                        self.add_triples(triples, filename)
                        total_triples += len(triples)
                        print(f"    Chunk {i+1}/{len(chunks)}: Extracted {len(triples)} triples.")
                
                print(f"  Finished {filename}. Total triples: {total_triples}")
                
            except Exception as e:
                print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    builder = KnowledgeGraphBuilder()
    try:
        data_dir = os.path.join("data", "raw")
        builder.process_directory(data_dir)
    finally:
        builder.close()
