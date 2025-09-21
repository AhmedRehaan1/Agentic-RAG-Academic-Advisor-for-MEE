import os, re, json, logging, sys
import json
import os, re, json, logging, sys
from typing import List, Dict, Any, Optional
from langchain.schema import Document
from config.config import JSON_FILES
def process_json_files() -> List[Document]:
    """JSON processing with better document chunking"""
    all_chunks = []

    print(" Starting  JSON chunking process...\n")

    for filename, category in JSON_FILES.items():
        try:
            print(f"Processing file: {filename} (Category: {category})")
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            #  logic to handle different JSON structures
            if category in ["courses_and_curriculum", "results_statistics"]:
                courses_list = []
                if category == "courses_and_curriculum":
                    courses_list = data.get("program_description", {}).get("courses", [])
                elif category == "results_statistics":
                    courses_list = data.get("courses", [])
                
                for item in courses_list:
                    doc = Document(
                        page_content=json.dumps(item, indent=2),
                        metadata={
                            "source": filename,
                            "category": category,
                            "course_code": item.get("course_code", "N/A"),
                            "course_name": item.get("course_name", "N/A"),
                            "semester": item.get("semester", "N/A")
                        }
                    )
                    all_chunks.append(doc)
                print(f"  -> Created {len(courses_list)} chunks.")

            elif category in ["general_info", "training_rules"]:
                main_content = data.get(category, {})
                count = 0
                for section_key, section_value in main_content.items():
                    doc = Document(
                        page_content=json.dumps({section_key: section_value}, indent=2),
                        metadata={
                            "source": filename,
                            "category": category,
                            "section": section_key
                        }
                    )
                    all_chunks.append(doc)
                    count += 1
                print(f"  -> Created {count} chunks.")

        except FileNotFoundError:
            logging.error(f"File '{filename}' not found. Skipping.")
        except json.JSONDecodeError:
            logging.error(f"Could not decode JSON from '{filename}'. Skipping.")

    print("\n--------------------------------------------------")
    print(f"✅ Total chunks created: {len(all_chunks)}")
    print("--------------------------------------------------\n")
    
    return all_chunks