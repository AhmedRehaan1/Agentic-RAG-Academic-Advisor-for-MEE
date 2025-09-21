from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import pandas as pd
import time
import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Union

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MEEDataExtractor:
    """Web scraper for extracting MEE course data from Cairo University"""
    
    def __init__(self, headless: bool = True, timeout: int = 20):
        """
        Initialize the web scraper for MEE course data extraction
        
        Args:
            headless: Run browser in headless mode
            timeout: Default timeout for web elements
        """
        self.driver = None
        self.wait = None
        self.timeout = timeout
        self.setup_driver(headless)
        
    def setup_driver(self, headless: bool) -> None:
        """Configure Chrome WebDriver with optimal settings"""
        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument("--headless")
            
            # Essential options for university websites
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, self.timeout)
            
            logger.info("WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Error setting up WebDriver: {e}")
            raise WebDriverException(f"Failed to initialize WebDriver: {e}")
        
    def navigate_to_results_page(self) -> bool:
        """Navigate to the main results page and handle any initial setup"""
        try:
            logger.info("Navigating to results page...")
            self.driver.get("https://chreg.eng.cu.edu.eg/chsresultstatistics.aspx?s=1")
            
            # Wait for page to load completely
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)  # Additional wait for dynamic content
            
            # Check if page loaded successfully
            if "error" in self.driver.title.lower() or "404" in self.driver.page_source:
                logger.warning("Page may not have loaded correctly")
                return False
            
            logger.info(f"Successfully navigated to: {self.driver.current_url}")
            return True
            
        except TimeoutException:
            logger.error("Timeout while navigating to page")
            return False
        except Exception as e:
            logger.error(f"Error navigating to page: {e}")
            return False
    
    def find_and_select_semester(self) -> bool:
        """Find and select Fall 2024 semester"""
        try:
            logger.info("Looking for semester selection...")
            
            # Common selectors for semester/term dropdowns
            semester_selectors = [
                "select[name*='semester']",
                "select[name*='term']", 
                "select[name*='period']",
                "select[id*='semester']",
                "select[id*='term']",
                "select[id*='period']",
                "select[name*='ddl']",
                "select[id*='ddl']"
            ]
            
            semester_dropdown = None
            for selector in semester_selectors:
                try:
                    semester_dropdown = self.driver.find_element(By.CSS_SELECTOR, selector)
                    logger.info(f"Found semester dropdown with selector: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not semester_dropdown:
                # Look for any dropdown that might contain semester info
                dropdowns = self.driver.find_elements(By.TAG_NAME, "select")
                for dropdown in dropdowns:
                    try:
                        options_text = [opt.text.lower() for opt in dropdown.find_elements(By.TAG_NAME, "option")]
                        if any("fall" in opt or "2024" in opt or "خريف" in opt for opt in options_text):
                            semester_dropdown = dropdown
                            logger.info("Found semester dropdown by content matching")
                            break
                    except Exception:
                        continue
            
            if semester_dropdown:
                select = Select(semester_dropdown)
                
                # Try to find Fall 2024 option
                fall_2024_patterns = [
                    "fall 2024", "fall2024", "f 2024", "f2024",
                    "خريف 2024", "2024 fall", "fall semester 2024",
                    "autumn 2024", "autumn2024"
                ]
                
                for option in select.options:
                    option_text = option.text.lower().strip()
                    if any(pattern in option_text for pattern in fall_2024_patterns):
                        select.select_by_visible_text(option.text)
                        logger.info(f"Selected semester: {option.text}")
                        time.sleep(2)
                        return True
                
                logger.warning("Fall 2024 not found, available options:")
                for option in select.options:
                    logger.warning(f"- {option.text}")
                    
            return False
            
        except Exception as e:
            logger.error(f"Error selecting semester: {e}")
            return False
    
    def find_and_select_mee_department(self) -> bool:
        """Find and select Mechatronics Engineering (MEE) department"""
        try:
            logger.info("Looking for department selection...")
            
            # Common selectors for department/program dropdowns
            dept_selectors = [
                "select[name*='department']",
                "select[name*='dept']",
                "select[name*='program']",
                "select[name*='major']",
                "select[id*='department']",
                "select[id*='dept']",
                "select[id*='program']",
                "select[id*='major']",
                "select[name*='ddl']",
                "select[id*='ddl']"
            ]
            
            dept_dropdown = None
            for selector in dept_selectors:
                try:
                    dropdowns = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for dropdown in dropdowns:
                        options_text = [opt.text.lower() for opt in dropdown.find_elements(By.TAG_NAME, "option")]
                        if any("mechatronics" in opt or "mee" in opt or "engineering" in opt for opt in options_text):
                            dept_dropdown = dropdown
                            logger.info(f"Found department dropdown with selector: {selector}")
                            break
                    if dept_dropdown:
                        break
                except NoSuchElementException:
                    continue
            
            if not dept_dropdown:
                # Fallback: check all dropdowns for MEE-related content
                all_dropdowns = self.driver.find_elements(By.TAG_NAME, "select")
                for dropdown in all_dropdowns:
                    try:
                        options_text = [opt.text.lower() for opt in dropdown.find_elements(By.TAG_NAME, "option")]
                        if any("mechatronics" in opt or "mee" in opt for opt in options_text):
                            dept_dropdown = dropdown
                            logger.info("Found department dropdown by content matching")
                            break
                    except Exception:
                        continue
            
            if dept_dropdown:
                select = Select(dept_dropdown)
                
                # MEE department patterns to look for
                mee_patterns = [
                    "mechatronics", "mee", "mechatronics engineering",
                    "هندسة الميكاترونيكس", "ميكاترونيكس"
                ]
                
                for option in select.options:
                    option_text = option.text.lower().strip()
                    if any(pattern in option_text for pattern in mee_patterns):
                        select.select_by_visible_text(option.text)
                        logger.info(f"Selected department: {option.text}")
                        time.sleep(2)
                        return True
                
                logger.warning("MEE department not found, available options:")
                for option in select.options:
                    logger.warning(f"- {option.text}")
                    
            return False
            
        except Exception as e:
            logger.error(f"Error selecting department: {e}")
            return False
    
    def submit_search_and_wait_for_results(self) -> bool:
        """Submit the search form and wait for results to load"""
        try:
            logger.info("Looking for submit button...")
            
            # Look for submit buttons
            submit_selectors = [
                "input[type='submit']",
                "button[type='submit']",
                "input[value*='Search']",
                "input[value*='View']",
                "input[value*='Show']",
                "button[contains(text(), 'Search')]",
                "button[contains(text(), 'View')]",
                "button[contains(text(), 'Show')]"
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    logger.info(f"Found submit button with selector: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if submit_button:
                # Scroll to button and click
                self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                time.sleep(1)
                submit_button.click()
                logger.info("Search submitted, waiting for results...")
                
                # Wait for results to load
                time.sleep(5)
                
                # Check if results table or content appeared
                possible_result_selectors = [
                    "table",
                    ".results",
                    "#results",
                    ".data-table",
                    ".course-data"
                ]
                
                for selector in possible_result_selectors:
                    try:
                        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        logger.info("Results loaded successfully")
                        return True
                    except TimeoutException:
                        continue
                        
                logger.info("Submit completed, proceeding with current page content")
                return True
            else:
                logger.warning("No submit button found")
                return False
                
        except Exception as e:
            logger.error(f"Error submitting search: {e}")
            return False
    
    def extract_course_data(self) -> List[Dict]:
        """Extract MEE course data and format as grade distribution"""
        try:
            course_data = []
            
            # Look for data tables
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            logger.info(f"Found {len(tables)} tables to process")
            
            for table_idx, table in enumerate(tables):
                logger.info(f"Processing table {table_idx + 1}...")
                
                try:
                    # Get headers
                    headers = []
                    header_rows = table.find_elements(By.TAG_NAME, "th")
                    if header_rows:
                        headers = [th.text.strip() for th in header_rows]
                    else:
                        # If no th tags, check first row
                        try:
                            first_row = table.find_element(By.TAG_NAME, "tr")
                            headers = [td.text.strip() for td in first_row.find_elements(By.TAG_NAME, "td")]
                        except NoSuchElementException:
                            continue
                    
                    logger.info(f"Headers found: {headers}")
                    
                    # Get data rows
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    
                    for row_idx, row in enumerate(rows[1:], 1):  # Skip header row
                        try:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if not cells:
                                continue
                                
                            row_data = [cell.text.strip() for cell in cells]
                            row_text = " ".join(row_data).lower()
                            
                            # Check if this row contains MEE-related data or concatenated course list
                            if self.contains_multiple_courses(row_text):
                                logger.info("Found concatenated course list, parsing...")
                                parsed_courses = self.parse_text_for_grades(" ".join(row_data))
                                if parsed_courses and isinstance(parsed_courses, list):
                                    for course in parsed_courses:
                                        course_with_grades = self.find_grades_for_course(course, table, headers)
                                        course_data.append(course_with_grades)
                                        logger.info(f"MEE course found: {course.get('course_code', 'Unknown')} - {course.get('course_name', 'Unknown')}")
                                elif parsed_courses:
                                    course_data.append(parsed_courses)
                            
                            # Also check for individual MEE courses
                            elif any(keyword in row_text for keyword in ["mee", "mechatronics", "ميكاترونيكس"]) or \
                               any(self.is_mee_course_code(cell) for cell in row_data):
                                
                                course_info = self.parse_course_row(row_data, headers)
                                if course_info:
                                    course_data.append(course_info)
                                    logger.info(f"MEE course found: {course_info.get('course_code', 'Unknown')} - {course_info.get('course_name', 'Unknown')}")
                        
                        except Exception as row_error:
                            logger.error(f"Error processing row {row_idx} in table {table_idx + 1}: {row_error}")
                            continue
                
                except Exception as table_error:
                    logger.error(f"Error processing table {table_idx + 1}: {table_error}")
                    continue
            
            # If no tables found, look for other data structures
            if not course_data:
                logger.info("No table data found, checking for other data structures...")
                course_data = self.extract_from_non_table_structure()
            
            logger.info(f"Extracted {len(course_data)} course records")
            return course_data
            
        except Exception as e:
            logger.error(f"Error extracting course data: {e}")
            return []
    
    def contains_multiple_courses(self, text: str) -> bool:
        """Check if text contains multiple course codes (concatenated list)"""
        try:
            course_pattern = r'[A-Z]{3,4}\d{3}:'
            matches = re.findall(course_pattern, text.upper())
            return len(matches) > 5
        except Exception:
            return False
    
    def find_grades_for_course(self, course_info: Dict, table, headers: List[str]) -> Dict:
        """Try to find grade data for a specific course in the table"""
        try:
            rows = table.find_elements(By.TAG_NAME, "tr")
            
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if not cells:
                    continue
                    
                row_data = [cell.text.strip() for cell in cells]
                row_text = " ".join(row_data).lower()
                
                # Check if this row mentions the course code
                course_code = course_info.get('course_code', '').lower()
                if course_code and course_code in row_text:
                    grades = self.extract_grades_from_row(row_data, headers)
                    if grades:
                        course_info['grades'] = grades
                        break
            
            return course_info
            
        except Exception as e:
            logger.error(f"Error finding grades for course {course_info.get('course_code', '')}: {e}")
            return course_info
    
    def extract_grades_from_row(self, row_data: List[str], headers: List[str]) -> Optional[Dict]:
        """Extract grade counts from a table row"""
        try:
            grades = {
                'A+': 0, 'A': 0, 'A-': 0,
                'B+': 0, 'B': 0, 'B-': 0,
                'C+': 0, 'C': 0, 'C-': 0,
                'D+': 0, 'D': 0, 'F': 0
            }
            
            for i, cell in enumerate(row_data):
                if cell.isdigit() and i < len(headers):
                    header = headers[i].strip()
                    grade = self.normalize_grade_header(header)
                    if grade in grades:
                        grades[grade] = int(cell)
            
            return grades if any(count > 0 for count in grades.values()) else None
            
        except Exception as e:
            logger.error(f"Error extracting grades from row: {e}")
            return None
    
    def is_mee_course_code(self, text: str) -> bool:
        """Check if text matches MEE course code pattern"""
        if not text or not isinstance(text, str):
            return False
            
        patterns = [
            r'^MEE\d{3}',
            r'^MDPS\d{3}',
            r'^MECH\d{3}',
            r'^MCT\d{3}',
        ]
        
        try:
            for pattern in patterns:
                if re.match(pattern, text.upper()):
                    return True
        except Exception:
            pass
        return False
    
    def parse_course_row(self, row_data: List[str], headers: List[str]) -> Optional[Dict]:
        """Parse a table row to extract course information and grades"""
        try:
            course_info = {
                'course_code': '',
                'course_name': '',
                'grades': {
                    'A+': 0, 'A': 0, 'A-': 0,
                    'B+': 0, 'B': 0, 'B-': 0,
                    'C+': 0, 'C': 0, 'C-': 0,
                    'D+': 0, 'D': 0, 'F': 0
                }
            }
            
            # Find course code and name
            for i, cell in enumerate(row_data):
                if self.is_mee_course_code(cell):
                    course_info['course_code'] = cell
                    if i + 1 < len(row_data) and not row_data[i + 1].isdigit():
                        course_info['course_name'] = row_data[i + 1]
                    break
            
            # If course code not found by pattern, check for MEE in any cell
            if not course_info['course_code']:
                for i, cell in enumerate(row_data):
                    if any(keyword in cell.lower() for keyword in ["mee", "mechatronics", "mdps"]):
                        parts = cell.split()
                        if len(parts) >= 2:
                            course_info['course_code'] = parts[0]
                            course_info['course_name'] = " ".join(parts[1:])
                        break
            
            # Extract grade counts
            for i, cell in enumerate(row_data):
                if cell.isdigit() and i < len(headers):
                    header = headers[i].strip()
                    grade = self.normalize_grade_header(header)
                    if grade in course_info['grades']:
                        course_info['grades'][grade] = int(cell)
            
            return course_info if course_info['course_code'] else None
            
        except Exception as e:
            logger.error(f"Error parsing course row: {e}")
            return None
    
    def normalize_grade_header(self, header: str) -> str:
        """Normalize header text to standard grade format"""
        if not header:
            return ""
            
        header = header.upper().strip()
        
        grade_mappings = {
            'A+': 'A+', 'APLUS': 'A+', 'A PLUS': 'A+',
            'A': 'A', 'A ': 'A',
            'A-': 'A-', 'AMINUS': 'A-', 'A MINUS': 'A-',
            'B+': 'B+', 'BPLUS': 'B+', 'B PLUS': 'B+',
            'B': 'B', 'B ': 'B',
            'B-': 'B-', 'BMINUS': 'B-', 'B MINUS': 'B-',
            'C+': 'C+', 'CPLUS': 'C+', 'C PLUS': 'C+',
            'C': 'C', 'C ': 'C',
            'C-': 'C-', 'CMINUS': 'C-', 'C MINUS': 'C-',
            'D+': 'D+', 'DPLUS': 'D+', 'D PLUS': 'D+',
            'D': 'D', 'D ': 'D',
            'F': 'F', 'FAIL': 'F', 'FAILED': 'F'
        }
        
        return grade_mappings.get(header, header)
    
    def extract_from_non_table_structure(self) -> List[Dict]:
        """Extract data from non-table structures"""
        try:
            course_data = []
            
            data_containers = self.driver.find_elements(By.CSS_SELECTOR, 
                ".course-item, .result-item, .data-row, [class*='course'], [class*='result']")
            
            for container in data_containers:
                try:
                    container_text = container.text.lower()
                    if any(keyword in container_text for keyword in ["mee", "mechatronics", "ميكاترونيكس", "mdps"]):
                        parsed_data = self.parse_text_for_grades(container.text)
                        if parsed_data:
                            if isinstance(parsed_data, list):
                                course_data.extend(parsed_data)
                            else:
                                course_data.append(parsed_data)
                except Exception as e:
                    logger.error(f"Error processing container: {e}")
                    continue
            
            return course_data
            
        except Exception as e:
            logger.error(f"Error extracting from non-table structure: {e}")
            return []
    
    def parse_text_for_grades(self, text: str) -> Union[List[Dict], Dict, None]:
        """Parse text content to extract course and grade information"""
        try:
            if not text:
                return None
                
            courses = []
            course_list = self.extract_individual_courses(text)
            
            for course_text in course_list:
                course_info = {
                    'course_code': '',
                    'course_name': '',
                    'grades': {
                        'A+': 0, 'A': 0, 'A-': 0,
                        'B+': 0, 'B': 0, 'B-': 0,
                        'C+': 0, 'C': 0, 'C-': 0,
                        'D+': 0, 'D': 0, 'F': 0
                    }
                }
                
                parsed_course = self.parse_individual_course(course_text)
                if parsed_course:
                    course_info['course_code'] = parsed_course['code']
                    course_info['course_name'] = parsed_course['name']
                    
                    grade_counts = self.extract_grade_counts_from_text(course_text)
                    if grade_counts:
                        course_info['grades'].update(grade_counts)
                    
                    if course_info['course_code']:
                        courses.append(course_info)
            
            return courses if courses else None
            
        except Exception as e:
            logger.error(f"Error parsing text for grades: {e}")
            return None
    
    def extract_individual_courses(self, text: str) -> List[str]:
        """Extract individual courses from a concatenated course list"""
        try:
            course_pattern = r'([A-Z]{3,4}\d{3}):([^A-Z]*?)(?=\s+[A-Z]{3,4}\d{3}:|$)'
            matches = re.findall(course_pattern, text)
            courses = []
            
            for match in matches:
                code = match[0].strip()
                name = match[1].strip().rstrip(':')
                
                if self.is_mee_related_course(code):
                    courses.append(f"{code}:{name}")
            
            return courses
            
        except Exception as e:
            logger.error(f"Error extracting individual courses: {e}")
            return []
    
    def is_mee_related_course(self, course_code: str) -> bool:
        """Check if a course is related to Mechatronics Engineering"""
        if not course_code:
            return False
            
        mee_prefixes = ['MEE', 'MEES', 'MEEN', 'MDPS', 'MDPN', 'MCNS']
        general_engineering = ['PHYS', 'MTHS', 'CMPS', 'CMPN', 'EPES', 'EPMN', 'EMCS']
        
        return any(course_code.startswith(prefix) for prefix in mee_prefixes + general_engineering)
    
    def parse_individual_course(self, course_text: str) -> Optional[Dict]:
        """Parse individual course string to extract code and name"""
        try:
            match = re.match(r'^([A-Z]{3,4}\d{3}):(.+)$', course_text.strip())
            if match:
                return {
                    'code': match.group(1).strip(),
                    'name': match.group(2).strip()
                }
            return None
        except Exception as e:
            logger.error(f"Error parsing individual course: {e}")
            return None
    
    def extract_grade_counts_from_text(self, text: str) -> Optional[Dict]:
        """Extract grade counts from text if present"""
        try:
            grade_counts = {}
            grade_patterns = {
                'A+': r'A\+\s*:\s*(\d+)', 'A': r'(?<![\+\-])A\s*:\s*(\d+)', 'A-': r'A\-\s*:\s*(\d+)',
                'B+': r'B\+\s*:\s*(\d+)', 'B': r'(?<![\+\-])B\s*:\s*(\d+)', 'B-': r'B\-\s*:\s*(\d+)',
                'C+': r'C\+\s*:\s*(\d+)', 'C': r'(?<![\+\-])C\s*:\s*(\d+)', 'C-': r'C\-\s*:\s*(\d+)',
                'D+': r'D\+\s*:\s*(\d+)', 'D': r'(?<![\+\-])D\s*:\s*(\d+)', 'F': r'F\s*:\s*(\d+)'
            }
            
            for grade, pattern in grade_patterns.items():
                match = re.search(pattern, text)
                if match:
                    grade_counts[grade] = int(match.group(1))
            
            return grade_counts if grade_counts else None
            
        except Exception as e:
            logger.error(f"Error extracting grade counts: {e}")
            return None
    
    def format_course_output(self, course_data: List[Dict]) -> str:
        """Format course data in the requested format"""
        formatted_output = []
        
        for course in course_data:
            if course.get('course_code') and course.get('course_name'):
                course_header = f"{course['course_code']} {course['course_name']}"
                formatted_output.append(course_header)
                
                grades_order = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'F']
                for grade in grades_order:
                    count = course['grades'].get(grade, 0)
                    grade_line = f"{grade.ljust(2)} : {count}"
                    formatted_output.append(grade_line)
                
                formatted_output.append("")
        
        return "\n".join(formatted_output)
    
    def save_formatted_output(self, course_data: List[Dict]) -> None:
        """Save data in the requested format"""
        try:
            if not course_data:
                logger.warning("No data to save")
                return
                
            formatted_text = self.format_course_output(course_data)
            
            # Create output directory if it doesn't exist
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            # Save to text file
            txt_path = output_dir / "mee_fall_2024_formatted.txt"
            with open(txt_path, "w", encoding='utf-8') as f:
                f.write(formatted_text)
            
            # Save raw data as JSON
            json_path = output_dir / "ewaw_      mee_fall_2024_raw_data.json"
            with open(json_path, "w", encoding='utf-8') as f:
                json.dump(course_data, f, ensure_ascii=False, indent=2)
            
            # Print results
            print("\n" + "="*50)
            print("MEE FALL 2024 COURSE RESULTS")
            print("="*50)
            print(formatted_text)
            
            logger.info(f"Formatted output saved to: {txt_path}")
            logger.info(f"Raw data saved to: {json_path}")
            
        except Exception as e:
            logger.error(f"Error saving formatted output: {e}")
    
    def save_data_to_files(self, course_data: List[Dict]) -> None:
        """Save extracted data in the requested format"""
        if not course_data:
            logger.warning("No data to save")
            return
        
        try:
            self.save_formatted_output(course_data)
            
            logger.info(f"Extracted {len(course_data)} MEE course records for Fall 2024")
            
            if course_data:
                print("\nCourse Summary:")
                for record in course_data:
                    if record.get('course_code'):
                        total_students = sum(record['grades'].values())
                        print(f"- {record['course_code']}: {total_students} students")
                    
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    def extract_mee_fall_2024_data(self) -> List[Dict]:
        """Main method to orchestrate the data extraction process"""
        try:
            logger.info("Starting MEE Fall 2024 data extraction...")
            
            # Step 1: Navigate to the page
            if not self.navigate_to_results_page():
                logger.error("Failed to navigate to results page")
                return []
            
            # Step 2: Handle potential form elements
            logger.info("Looking for form controls...")
            
            semester_selected = self.find_and_select_semester()
            dept_selected = self.find_and_select_mee_department()
            
            # Step 3: Submit if form controls were found
            if semester_selected or dept_selected:
                if not self.submit_search_and_wait_for_results():
                    logger.warning("Could not submit search, proceeding with current page content")
            
            # Step 4: Extract the data
            course_data = self.extract_course_data()
            
            # Step 5: Save the data
            self.save_data_to_files(course_data)
            
            return course_data
            
        except Exception as e:
            logger.error(f"Error in main extraction process: {e}")
            return []
        finally:
            self.cleanup()
    
    def debug_page_structure(self) -> None:
        """Debug method to understand the page structure"""
        try:
            logger.info("=== DEBUG: Page Structure Analysis ===")
            
            print(f"Page Title: {self.driver.title}")
            
            # Check for forms
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            print(f"Forms found: {len(forms)}")
            
            # Check for dropdowns
            dropdowns = self.driver.find_elements(By.TAG_NAME, "select")
            print(f"Dropdowns found: {len(dropdowns)}")
            
            for i, dropdown in enumerate(dropdowns):
                name = dropdown.get_attribute('name') or 'N/A'
                id_attr = dropdown.get_attribute('id') or 'N/A'
                print(f"Dropdown {i+1} name/id: {name} / {id_attr}")
                options = dropdown.find_elements(By.TAG_NAME, "option")
                option_texts = [opt.text for opt in options[:5]]
                print(f"  Options: {option_texts}...")
            
            # Check for tables
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            print(f"Tables found: {len(tables)}")
            
            # Check for common data containers
            data_divs = self.driver.find_elements(By.CSS_SELECTOR, 
                "[class*='result'], [class*='course'], [class*='data'], [id*='result'], [id*='course']")
            print(f"Potential data containers: {len(data_divs)}")
            
            # Check page source for MEE mentions
            page_source = self.driver.page_source.lower()
            mee_mentions = page_source.count("mee") + page_source.count("mechatronics")
            print(f"MEE/Mechatronics mentions in source: {mee_mentions}")
            
            # Save debug info
            debug_path = Path("output/page_debug.html")
            debug_path.parent.mkdir(exist_ok=True)
            with open(debug_path, "w", encoding='utf-8') as f:
                f.write(self.driver.page_source)
            print(f"Page source saved to {debug_path}")
            
        except Exception as e:
            logger.error(f"Debug error: {e}")
    
    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


class AdvancedMEEExtractor(MEEDataExtractor):
    """Enhanced extractor with advanced techniques for complex sites"""
    
    def wait_for_dynamic_content(self, timeout: int = 30) -> bool:
        """Wait for dynamic content to load using multiple strategies"""
        strategies = [
            self.wait_for_loading_to_complete,
            lambda: self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "table"))),
            self.wait_for_ajax_complete,
        ]
        
        for strategy in strategies:
            try:
                strategy()
                return True
            except TimeoutException:
                continue
        
        return False
    
    def wait_for_loading_to_complete(self) -> bool:
        """Wait for common loading indicators to disappear"""
        loading_selectors = [
            ".loading", "#loading", ".spinner", ".loader",
            "[style*='loading']", ".progress", ".wait"
        ]
        
        for selector in loading_selectors:
            try:
                self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, selector)))
                return True
            except (NoSuchElementException, TimeoutException):
                continue
        
        return True
    
    def wait_for_ajax_complete(self) -> bool:
        """Wait for AJAX requests to complete"""
        try:
            return self.wait.until(
                lambda driver: driver.execute_script("return jQuery.active == 0") if 
                driver.execute_script("return typeof jQuery !== 'undefined'") else True
            )
        except Exception:
            return True
    
    def extract_with_javascript(self) -> List:
        """Use JavaScript execution for complex extractions"""
        try:
            js_script = """
            var meeData = [];
            
            // Look for tables containing MEE data
            var tables = document.querySelectorAll('table');
            tables.forEach(function(table) {
                var rows = table.querySelectorAll('tr');
                rows.forEach(function(row) {
                    var rowText = row.textContent.toLowerCase();
                    if (rowText.includes('mee') || rowText.includes('mechatronics') || rowText.includes('ميكاترونيكس')) {
                        var cells = row.querySelectorAll('td, th');
                        var rowData = Array.from(cells).map(cell => cell.textContent.trim());
                        meeData.push(rowData);
                    }
                });
            });
            
            // Look for div-based data
            var dataContainers = document.querySelectorAll('[class*="course"], [class*="result"], [id*="course"], [id*="result"]');
            dataContainers.forEach(function(container) {
                var containerText = container.textContent.toLowerCase();
                if (containerText.includes('mee') || containerText.includes('mechatronics')) {
                    meeData.push({
                        text: container.textContent.trim(),
                        html: container.outerHTML
                    });
                }
            });
            
            return meeData;
            """
            
            result = self.driver.execute_script(js_script)
            return result or []
            
        except Exception as e:
            logger.error(f"Error executing JavaScript extraction: {e}")
            return []
    
    def convert_js_data_to_course_format(self, js_data: List) -> List[Dict]:
        """Convert JavaScript extracted data to proper course format"""
        try:
            formatted_courses = []
            
            for item in js_data:
                if isinstance(item, dict) and 'text' in item:
                    parsed = self.parse_text_for_grades(item['text'])
                    if parsed:
                        if isinstance(parsed, list):
                            formatted_courses.extend(parsed)
                        else:
                            formatted_courses.append(parsed)
                elif isinstance(item, list):
                    # Handle array data from table rows
                    concatenated_text = ' '.join([str(cell) for cell in item])
                    if ':' in concatenated_text and len([cell for cell in item if ':' in str(cell)]) > 3:
                        parsed_courses = self.parse_text_for_grades(concatenated_text)
                        if parsed_courses and isinstance(parsed_courses, list):
                            formatted_courses.extend(parsed_courses)
                    else:
                        course_info = self.parse_row_array_for_course(item)
                        if course_info:
                            formatted_courses.append(course_info)
            
            return formatted_courses
            
        except Exception as e:
            logger.error(f"Error converting JS data: {e}")
            return []
    
    def parse_row_array_for_course(self, row_array: List) -> Optional[Dict]:
        """Parse array of cell data to extract course information"""
        try:
            course_info = {
                'course_code': '',
                'course_name': '',
                'grades': {
                    'A+': 0, 'A': 0, 'A-': 0,
                    'B+': 0, 'B': 0, 'B-': 0,
                    'C+': 0, 'C': 0, 'C-': 0,
                    'D+': 0, 'D': 0, 'F': 0
                }
            }
            
            # Find course code in the array
            for i, cell in enumerate(row_array):
                if self.is_mee_course_code(str(cell)):
                    course_info['course_code'] = str(cell)
                    if i + 1 < len(row_array):
                        next_cell = str(row_array[i + 1])
                        if not next_cell.isdigit() and not self.normalize_grade_header(next_cell) in course_info['grades']:
                            course_info['course_name'] = next_cell
                    break
            
            # Extract grade counts from numeric cells
            grade_keywords = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'F']
            numeric_values = [int(cell) for cell in row_array if str(cell).isdigit()]
            
            if len(numeric_values) == 12:
                for i, grade in enumerate(grade_keywords):
                    course_info['grades'][grade] = numeric_values[i]
            
            return course_info if course_info['course_code'] else None
            
        except Exception as e:
            logger.error(f"Error parsing row array: {e}")
            return None


def run_mee_extraction() -> List[Dict]:
    """Run the MEE data extraction with error handling and multiple strategies"""
    
    print("=== MEE Fall 2024 Course Data Extraction ===\n")
    
    extractor = None
    advanced_extractor = None
    
    try:
        # Try basic extraction first
        extractor = MEEDataExtractor(headless=False)
        
        if extractor.navigate_to_results_page():
            extractor.debug_page_structure()
            course_data = extractor.extract_mee_fall_2024_data()
            
            # If no data found, try advanced approach
            if not course_data:
                logger.info("No data found with standard approach, trying advanced extraction...")
                extractor.cleanup()
                
                advanced_extractor = AdvancedMEEExtractor(headless=False)
                if advanced_extractor.navigate_to_results_page():
                    js_data = advanced_extractor.extract_with_javascript()
                    if js_data:
                        formatted_js_data = advanced_extractor.convert_js_data_to_course_format(js_data)
                        if formatted_js_data:
                            advanced_extractor.save_formatted_output(formatted_js_data)
                            course_data = formatted_js_data
                
                if advanced_extractor:
                    advanced_extractor.cleanup()
            
            return course_data or []
            
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return []
    finally:
        # Cleanup in finally block to ensure resources are freed
        if extractor:
            try:
                extractor.cleanup()
            except Exception:
                pass
        if advanced_extractor:
            try:
                advanced_extractor.cleanup()
            except Exception:
                pass


if __name__ == "__main__":
    # Check requirements
    print("Required packages: selenium, pandas")
    print("Ensure ChromeDriver is installed and accessible\n")
    
    try:
        # Run extraction
        extracted_data = run_mee_extraction()
        
        if extracted_data:
            print(f"\n✅ Successfully extracted {len(extracted_data)} MEE course records")
            print("Data saved to output directory")
        else:
            print("\n❌ No MEE course data found for Fall 2024")
            print("Possible reasons:")
            print("- Fall 2024 semester not yet available")
            print("- MEE department not offered in Fall 2024") 
            print("- Page structure has changed")
            print("- Page requires authentication")
            print("- Network connectivity issues")
    
    except KeyboardInterrupt:
        print("\n⚠️ Extraction interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Extraction failed: {e}")