import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os

def load_existing_links():
    """Load existing links from Excel file if it exists"""
    excel_filename = 'linksmanagement_links.xlsx'
    if os.path.exists(excel_filename):
        try:
            df = pd.read_excel(excel_filename)
            return df.to_dict('records')
        except Exception as e:
            print(f"Error loading existing links: {str(e)}")
    return []

def save_links(links):
    """Save links to Excel file"""
    if links:
        df = pd.DataFrame(links)
        excel_filename = 'linksmanagement_links.xlsx'
        
        # Save with formatting
        with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Links')
            
            # Get worksheet
            worksheet = writer.sheets['Links']
            
            # Adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column = [cell for cell in column]
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2)
                worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
        
        print(f"Links saved to {excel_filename}")
        print(f"Total links: {len(links)}")

def update_links(existing_links, new_links):
    """Update existing links with new data"""
    # Convert lists to dictionaries for easier comparison
    existing_dict = {link['URL']: link for link in existing_links}
    new_dict = {link['URL']: link for link in new_links}
    
    # Update existing links and add new ones
    for url, new_link in new_dict.items():
        if url in existing_dict:
            # Update existing link
            existing_dict[url].update(new_link)
            existing_dict[url]['Last Updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            # Add new link
            new_link['First Scraped'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_link['Last Updated'] = new_link['First Scraped']
            existing_dict[url] = new_link
    
    # Convert back to list
    updated_links = list(existing_dict.values())
    
    # Add status for removed links
    removed_urls = set(existing_dict.keys()) - set(new_dict.keys())
    for url in removed_urls:
        existing_dict[url]['Status'] = 'Removed'
        existing_dict[url]['Last Updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return updated_links

def scrape_linksmanagement():
    # Dashboard URL
    dashboard_url = "https://newcp.linksmanagement.com/dashboard"
    
    try:
        # Load existing links
        existing_links = load_existing_links()
        print(f"Loaded {len(existing_links)} existing links")
        
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Initialize the Chrome driver
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 20)  # Wait up to 20 seconds for elements
        
        # Login URL
        login_url = "https://www.linksmanagement.com/sign-in/"
        print("Accessing login page...")
        driver.get(login_url)
        
        # Wait for login form to load
        wait.until(EC.presence_of_element_located((By.ID, "form-log-in")))
        
        # Find and fill login form
        email_input = driver.find_element(By.CSS_SELECTOR, "#form-log-in > div:nth-child(1) > input")
        password_input = driver.find_element(By.CSS_SELECTOR, "#form-log-in > div:nth-child(2) > input")
        
        email_input.send_keys("zeynel6776@gmail.com")
        password_input.send_keys("1899774152")
        
        # Submit login form
        login_button = driver.find_element(By.CSS_SELECTOR, "#form-log-in button[type='submit']")
        login_button.click()
        
        # Wait for login to complete and redirect to dashboard
        print("Logging in...")
        time.sleep(5)  # Wait for redirect
        
        # Access dashboard
        print("\nAccessing dashboard...")
        driver.get(dashboard_url)
        
        # Wait for dashboard content to load
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".link-block")))
        
        new_links = []
        current_page = 1
        total_pages = 2  # Set to 200 pages as specified
        
        while current_page <= total_pages:
            print(f"\nScraping page {current_page} of {total_pages}...")
            
            try:
                # Wait for link blocks to be visible
                link_blocks = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".link-block")))
                
                if not link_blocks:
                    print(f"No link blocks found on page {current_page}")
                    break
                
                print(f"Found {len(link_blocks)} links on page {current_page}")
                
                # Extract data from each link block
                for block in link_blocks:
                    try:
                        # Get URL
                        url_elem = block.find_element(By.CSS_SELECTOR, ".h4.font-weight-normal.mb-1 a")
                        url = url_elem.get_attribute("href")
                        
                        # Get category and language info
                        info_div = block.find_element(By.CSS_SELECTOR, ".d-flex.flex-column.small.width-250.font-weight-500")
                        category = info_div.find_element(By.CSS_SELECTOR, "div").text.replace("Category:", "").strip()
                        language = info_div.find_element(By.CSS_SELECTOR, "div:nth-of-type(2)").text.strip()
                        
                        # Get metrics
                        metrics = block.find_elements(By.CSS_SELECTOR, ".info-stats-block .indicator")
                        da = pa = sb = monthly_price = permanent_price = ''
                        
                        for metric in metrics:
                            text = metric.text.strip()
                            if 'DA:' in text:
                                da = text.replace('DA:', '').strip()
                            elif 'PA:' in text:
                                pa = text.replace('PA:', '').strip()
                            elif 'SB:' in text:
                                sb = text.replace('SB:', '').strip()
                            elif 'Monthly Price' in text:
                                monthly_price = text.replace('Monthly Price', '').strip()
                            elif 'Permanent Price' in text:
                                permanent_price = text.replace('Permanent Price', '').strip()
                        
                        # Add to results
                        new_links.append({
                            'URL': url,
                            'Category': category,
                            'Language': language,
                            'DA': da,
                            'PA': pa,
                            'SB': sb,
                            'Monthly Price': monthly_price,
                            'Permanent Price': permanent_price,
                            'Page': current_page,
                            'Scraped Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        
                    except Exception as e:
                        print(f"Error processing link block: {str(e)}")
                        continue
                
                # Save progress every 10 pages
                if current_page % 10 == 0:
                    updated_links = update_links(existing_links, new_links)
                    save_links(updated_links)
                
                # Click next page
                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, "ngb-pagination li.page-item:last-child a")
                    next_button.click()
                    time.sleep(2)  # Wait for page to load
                    current_page += 1
                except NoSuchElementException:
                    print("Could not find next page button")
                    break
                except Exception as e:
                    print(f"Error navigating to next page: {str(e)}")
                    break
                
            except TimeoutException:
                print(f"Timeout waiting for page {current_page} to load")
                break
            except Exception as e:
                print(f"Error processing page {current_page}: {str(e)}")
                break
        
        # Final update and save
        updated_links = update_links(existing_links, new_links)
        save_links(updated_links)
        
        # Close the browser
        driver.quit()
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    scrape_linksmanagement()
