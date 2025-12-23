import streamlit as st
from neo4j import GraphDatabase
from pyvis.network import Network
import os
from dotenv import load_dotenv
import tempfile

load_dotenv()

# Page Config
st.set_page_config(page_title="CRDC Knowledge Graph", layout="wide")

# Sidebar
st.sidebar.title("Connection Settings")
uri = st.sidebar.text_input("Neo4j URI", "bolt://localhost:7687")
user = st.sidebar.text_input("Username", "neo4j")
password = st.sidebar.text_input("Password", os.getenv("NEO4J_PASSWORD", "cotton-crdc-pw"), type="password")

@st.cache_resource
def get_driver(uri, user, password):
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        # Test connection
        driver.verify_connectivity()
        return driver
    except Exception as e:
        raise e

# Initialize driver
driver = None
try:
    driver = get_driver(uri, user, password)
    st.sidebar.success("✅ Connected to Neo4j")
except Exception as e:
    st.sidebar.error(f"❌ Connection failed: {e}")
    st.error("Cannot connect to Neo4j. Please check that Neo4j is running and credentials are correct.")
    st.stop()

# Main Area
st.title("CRDC Knowledge Graph Pilot")

# Search
search_term = st.text_input("Search for an Entity (e.g., 'CRDC')", "")

if search_term:
    with driver.session() as session:
        # Fetch neighborhood - works with any node labels
        query = """
        MATCH (n)-[r]-(m)
        WHERE n.name CONTAINS $term
        RETURN n.name AS source, labels(n)[0] AS source_type, 
               type(r) AS relationship, 
               m.name AS target, labels(m)[0] AS target_type
        LIMIT 50
        """
        result = session.run(query, term=search_term)
        data = [record.data() for record in result]
        
        if not data:
            st.warning("No results found.")
        else:
            # Tabular View
            st.subheader("Relationships")
            st.dataframe(data)
            
            # Graph View
            st.subheader("Graph Visualization")
            net = Network(height="600px", width="100%", bgcolor="#222222", font_color="white")
            
            sources = set()
            targets = set()
            
            for item in data:
                src = item['source']
                dst = item['target']
                rel = item['relationship']
                
                net.add_node(src, src, title=src, color="#97c2fc")
                net.add_node(dst, dst, title=dst, color="#ffff00")
                net.add_edge(src, dst, title=rel, label=rel)
                
            # Physics settings
            net.repulsion(node_distance=200, central_gravity=0.2, spring_length=200, spring_strength=0.05, damping=0.09)
            
            # Save and display
            with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
                net.save_graph(tmp.name)
                with open(tmp.name, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                st.components.v1.html(html_content, height=600)
                
else:
    st.info("Enter a search term to visualize the graph.")
    
    # Stats
    with driver.session() as session:
        count = session.run("MATCH (n) RETURN count(n) as c").single()["c"]
        st.metric("Total Nodes in Graph", count)
