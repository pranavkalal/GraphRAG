import os
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

load_dotenv()

class DocumentParser:
    def __init__(self):
        endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
        
        if not endpoint or not key:
            raise ValueError("Azure Document Intelligence credentials not found in environment variables.")
            
        self.client = DocumentIntelligenceClient(
            endpoint=endpoint, 
            credential=AzureKeyCredential(key)
        )

    def parse_pdf(self, file_path: str) -> str:
        """
        Parses a PDF file using Azure Document Intelligence 'prebuilt-layout' model
        and returns the content as Markdown.
        """
        print(f"Parsing {file_path}...")
        
        with open(file_path, "rb") as f:
            poller = self.client.begin_analyze_document(
                "prebuilt-layout", 
                body=f,
                content_type="application/octet-stream",
                output_content_format="markdown" # Request Markdown output
            )
            
        result = poller.result()
        
        # Azure Doc Intel with 'output_content_format="markdown"' returns the full markdown in `content`
        if hasattr(result, "content"):
            return result.content
        
        # Fallback if for some reason markdown isn't directly available (older versions/models)
        # But prebuilt-layout with output_content_format="markdown" should work.
        return ""

if __name__ == "__main__":
    # Test run
    try:
        parser = DocumentParser()
        # Find a test file
        test_dir = os.path.join("data", "raw")
        if os.path.exists(test_dir):
            files = [f for f in os.listdir(test_dir) if f.endswith(".pdf")]
            if files:
                test_file = os.path.join(test_dir, files[0])
                md_content = parser.parse_pdf(test_file)
                print(f"--- Parsed Content Preview ({files[0]}) ---")
                print(md_content[:500])
            else:
                print("No PDF files found in data/raw for testing.")
        else:
            print("data/raw directory not found.")
    except Exception as e:
        print(f"Parser test failed: {e}")
