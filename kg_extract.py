from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

# Define specific relationship types for CRDC domain
RELATIONSHIP_TYPES = Literal[
    "FUNDS",              # CRDC funds a project
    "MANAGES",            # Organization/person manages project
    "PARTNERS_WITH",      # Partnership between organizations
    "REPORTS_TO",         # Governance/reporting structure
    "LEADS",              # Person leads project/initiative
    "ALLOCATED_TO",       # Budget allocated to area/project
    "FOCUSES_ON",         # Strategic focus area
    "COLLABORATES_WITH",  # Research collaboration
    "DELIVERS",           # Project delivers outcome
    "PART_OF",            # Hierarchical relationship
]

# Define entity types
ENTITY_TYPES = Literal[
    "Organization",   # CRDC, CSIRO, Universities
    "Project",        # R&D projects, initiatives
    "Person",         # Researchers, executives
    "FundingArea",    # Investment portfolios
    "StrategicGoal",  # Objectives, outcomes
    "Amount",         # Dollar amounts
    "Program",        # RD&E programs
]


class CRDCTriple(BaseModel):
    """
    Represents a knowledge graph triple with typed entities and relationships.
    """
    subject: str = Field(description="The source entity name, normalized (e.g., 'CRDC', 'Dr. Jane Smith').")
    subject_type: str = Field(description="Type of subject: Organization, Project, Person, FundingArea, StrategicGoal, Amount, or Program.")
    relationship: str = Field(description="Relationship type: FUNDS, MANAGES, PARTNERS_WITH, REPORTS_TO, LEADS, ALLOCATED_TO, FOCUSES_ON, COLLABORATES_WITH, DELIVERS, or PART_OF.")
    object: str = Field(description="The target entity name, normalized.")
    object_type: str = Field(description="Type of object: Organization, Project, Person, FundingArea, StrategicGoal, Amount, or Program.")


class CRDCTripleList(BaseModel):
    triples: List[CRDCTriple]


class KGExtractor:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        
        # CRDC-specific extraction prompt with examples
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Knowledge Graph engineer specializing in agricultural R&D organizations.
Your task is to extract structured triples from CRDC (Cotton Research and Development Corporation) documents.

ENTITY TYPES:
- Organization: CRDC, CSIRO, universities, industry bodies
- Project: Named R&D projects or initiatives  
- Person: Researchers, executives, board members
- FundingArea: Investment portfolios (e.g., "Crop Protection", "Sustainability")
- StrategicGoal: Objectives, outcomes, KPIs
- Amount: Dollar figures (e.g., "$2.5 million")
- Program: Named programs (e.g., "Cotton Seed Distributors", "myBMP")

RELATIONSHIP TYPES:
- FUNDS: Financial investment (CRDC FUNDS Project X)
- MANAGES: Oversight responsibility
- PARTNERS_WITH: Formal partnerships
- REPORTS_TO: Governance hierarchy
- LEADS: Leadership role
- ALLOCATED_TO: Budget allocation
- FOCUSES_ON: Strategic priorities
- COLLABORATES_WITH: Research collaboration
- DELIVERS: Project outcomes
- PART_OF: Hierarchical containment

IMPORTANT:
- Normalize entity names (use "CRDC" not "the CRDC" or "Cotton Research and Development Corporation")
- Extract specific relationships, not generic ones
- Include dollar amounts as Amount entities when mentioned with investments"""),
            
            ("user", """Extract all meaningful triples from this CRDC document text:

{text}

Return a JSON object with 'triples' containing entity-relationship-entity tuples.""")
        ])

    def extract_triples(self, text_chunk: str) -> List[CRDCTriple]:
        """
        Extracts structured CRDC triples from text.
        """
        structured_llm = self.llm.with_structured_output(CRDCTripleList)
        chain = self.prompt | structured_llm
        
        try:
            result = chain.invoke({"text": text_chunk})
            return result.triples
        except Exception as e:
            print(f"Error extracting triples: {e}")
            return []
