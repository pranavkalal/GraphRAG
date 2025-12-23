import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

uri = "bolt://localhost:7687"
user = "neo4j"
password = os.getenv("NEO4J_PASSWORD", "cotton-crdc-pw")

try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        result = session.run("MATCH (n) RETURN count(n) as count")
        count = result.single()["count"]
        print(f"Node count: {count}")
        
        if count > 0:
            print("\nSample Relationships:")
            result = session.run("MATCH (s)-[r]->(o) RETURN s.name, type(r), o.name LIMIT 5")
            for record in result:
                print(f"{record['s.name']} -[{record['type(r)']}]-> {record['o.name']}")
    driver.close()
except Exception as e:
    print(f"Query failed: {e}")
