import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from decouple import config


def load_accounts():
    """Load accounts from .env"""
    accounts = []
    i = 1
    while True:
        name = config(f"ACC{i}_NAME", default=None)
        dp_id = config(f"ACC{i}_DP_ID", default=None)
        username = config(f"ACC{i}_USERNAME", default=None)
        password = config(f"ACC{i}_PASSWORD", default=None)
        crn = config(f"ACC{i}_CRN", default=None)
        pin = config(f"ACC{i}_PIN", default=None)
        lot = config(f"ACC{i}_LOT", default=None)

        if not all([name, dp_id, username, password]):
            break

        accounts.append({
            "name": name,
            "dp_id": dp_id,
            "username": username,
            "password": password,
            "crn": crn,
            "pin": pin,
            "lot": lot,
        })
        i += 1

    return accounts


def select_dp(driver, dp_id):
    """Select DP from Select2 dropdown"""
    try:
        dropdown = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "selectBranch"))
        )
        dropdown.click()
        time.sleep(0.5)

        # Search DP ID
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='search']"))
        )
        search_box.clear()
        search_box.send_keys(dp_id)
        time.sleep(0.5)

        # Press Enter to select DP
        search_box.send_keys(Keys.ENTER)
        time.sleep(1)

        print(f"✅ DP selected: {dp_id}")

    except Exception as e:
        raise Exception(f"Failed to select DP: {e}")


def enter_username(driver: webdriver.Chrome, username: str, timeout: int = 15):
    """
    Enters a username character by character into a field with Angular compatibility.

    Args:
        driver (webdriver.Chrome): The Selenium WebDriver instance.
        username (str): The username string to be entered.
        timeout (int): The maximum time to wait for the element in seconds.

    Raises:
        TimeoutException: If the username field is not found within the timeout.
        Exception: If the final value in the field does not match the input.
    """
    if not isinstance(username, str):
        print("⚠️ Warning: The provided username is not a string. Attempting to convert.")
        username = str(username)

    try:
        # Wait for the username field to be present and clickable
        username_field = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.ID, "username"))
        )

        # Clear the field using a robust method
        username_field.clear()
        time.sleep(0.3)  # Small delay for Angular to register the clear event

        print(f"Typing username: {username}")
        # Type each character with a small delay
        for char in username:
            username_field.send_keys(char)
            time.sleep(0.2)

        # Trigger Angular events
        driver.execute_script("""arguments[0].dispatchEvent(new Event('input', { bubbles: true })); arguments[0].dispatchEvent(new Event('change', { bubbles: true }));""", username_field)

        # Verify the entered value
        final_value = username_field.get_attribute('value')
        if final_value != username:
            raise ValueError(f"❌ Username mismatch: expected '{username}', but got '{final_value}'")

        print(f"✅ Username entered successfully: {final_value}")

    except Exception as e:
        print(f"An error occurred while entering the username: {e}")
        raise


def enter_password(driver, password):
    """Fill password"""
    password_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "password"))
    )

    password_field.click()
    password_field.clear()
    password_field.send_keys(password)
    print("🔑 Password entered successfully")


def login(driver, acc):
    """Login to MeroShare and navigate directly to My ASBA page"""
    driver.get("https://meroshare.cdsc.com.np/#/login")

    # Wait for login form
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "username"))
    )

    # STEP 1: Select DP
    select_dp(driver, acc["dp_id"])

    # STEP 2: Enter username properly
    enter_username(driver, acc["username"])

    # STEP 3: Enter password
    enter_password(driver, acc["password"])

    # STEP 4: Click Login button
    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Login')]"))
    )
    login_button.click()
    print(f"🔐 Attempting login for {acc['name']}...")

    # ✅ Wait for dashboard or ASBA page after login
    try:
        WebDriverWait(driver, 25).until(
            EC.any_of(
                EC.presence_of_element_located((By.CLASS_NAME, "sidebar")),
                EC.url_contains("dashboard")
            )
        )
        print("✅ Login successful!")

        # 🔄 Navigate directly to ASBA page after login
        navigate_to_asba(driver)

    except Exception as e:
        print(f"⚠️ Warning: Could not verify dashboard load: {e}")
        print(f"Current URL: {driver.current_url}")
        print("🔄 Trying to navigate to ASBA page anyway...")
        navigate_to_asba(driver)


def navigate_to_asba(driver):
    """Navigate to My ASBA section using direct URL"""
    try:
        print("🔍 Navigating directly to My ASBA page...")
        driver.get("https://meroshare.cdsc.com.np/#/asba")
        time.sleep(3)  # Wait for page to load

        # Verify ASBA page loaded
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'Apply for Issue') or contains(text(),'Current Issue')]")
            )
        )
        print("✅ Successfully navigated to My ASBA page")

    except Exception as e:
        print(f"❌ Failed to navigate to My ASBA: {e}")
        try:
            print(f"Current URL: {driver.current_url}")
            print(f"Page title: {driver.title}")
        except:
            pass
        raise


def select_ipo_and_apply(driver):
    """Find specific IPO by name/symbol and click Apply"""
    try:
        ipo_name = config("APPLY_IPO", default="")
        if not ipo_name:
            raise Exception("APPLY_IPO not found in .env file")
        
        print(f"🔍 Looking for IPO: {ipo_name}")
        
        # Wait for the IPO list to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'table') or contains(@class, 'list') or contains(@class, 'company')]"))
        )
        time.sleep(2)
        
        # Extract key parts from IPO name for flexible matching
        ipo_parts = []
        if "(" in ipo_name and ")" in ipo_name:
            # Extract both full name and code in parentheses
            full_part = ipo_name.split("(")[0].strip()
            code_part = ipo_name.split("(")[1].split(")")[0].strip()
            ipo_parts.extend([ipo_name, full_part, code_part])
        else:
            ipo_parts.append(ipo_name)
        
        # Add variations for better matching
        for part in ipo_parts.copy():
            # Add uppercase version
            ipo_parts.append(part.upper())
            # Add version without spaces
            ipo_parts.append(part.replace(" ", ""))
            # Add version with different spacing
            ipo_parts.append(part.replace(" ", "").upper())
        
        print(f"🔍 Searching for IPO variations: {ipo_parts}")
        
        apply_button = None
        ipo_number = None
        
        # Try to find IPO with enhanced selectors including btn-issue class
        for search_term in ipo_parts:
            if apply_button:
                break
                
            ipo_selectors = [
                # Look for Apply button or btn-issue class near the IPO name
                f"//span[contains(@class,'company-name') and contains(text(),'{search_term}')]/ancestor::div[contains(@class,'row')]//button[contains(@class,'btn-issue') or contains(text(),'Apply')]",
                f"//div[contains(text(),'{search_term}')]/ancestor::div[contains(@class,'row')]//button[contains(@class,'btn-issue') or contains(text(),'Apply')]",
                f"//td[contains(text(),'{search_term}')]/following-sibling::td//button[contains(@class,'btn-issue') or contains(text(),'Apply')]",
                f"//tr[contains(.,'{search_term}')]//button[contains(@class,'btn-issue') or contains(text(),'Apply')]",
                # Case insensitive search
                f"//div[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'{search_term.lower()}')]//button[contains(@class,'btn-issue') or contains(text(),'Apply')]",
                # Broader search in any container
                f"//div[contains(.,'{search_term}')]//button[contains(@class,'btn-issue') or contains(text(),'Apply')]"
            ]
            
            for i, selector in enumerate(ipo_selectors):
                try:
                    print(f"🔍 Trying selector {i+1} with term '{search_term}'...")
                    apply_button = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    print(f"✅ Found IPO using selector {i+1} with term '{search_term}'")
                    
                    try:
                        # Look for data attributes or hidden fields that might contain the IPO ID/number
                        parent_row = apply_button.find_element(By.XPATH, "./ancestor::div[contains(@class,'row') or contains(@class,'company')][1]")
                        
                        # Try to find IPO number in various ways
                        possible_number_elements = [
                            parent_row.find_elements(By.XPATH, ".//input[@type='hidden']"),
                            parent_row.find_elements(By.XPATH, ".//*[@data-id or @data-ipo-id or @data-number]"),
                            driver.find_elements(By.XPATH, f"//div[contains(.,'{search_term}')]//*[@data-id or @data-ipo-id]")
                        ]
                        
                        for elements in possible_number_elements:
                            for element in elements:
                                value = element.get_attribute('value') or element.get_attribute('data-id') or element.get_attribute('data-ipo-id') or element.get_attribute('data-number')
                                if value and value.isdigit():
                                    ipo_number = value
                                    print(f"✅ Found IPO number: {ipo_number}")
                                    break
                            if ipo_number:
                                break
                        
                        # If no number found in attributes, try to extract from onclick or href
                        if not ipo_number:
                            onclick = apply_button.get_attribute('onclick') or ''
                            href = apply_button.get_attribute('href') or ''
                            
                            import re
                            number_match = re.search(r'\d+', onclick + href)
                            if number_match:
                                ipo_number = number_match.group()
                                print(f"✅ Extracted IPO number from attributes: {ipo_number}")
                    
                    except Exception as e:
                        print(f"⚠️ Could not extract IPO number: {e}")
                    
                    break
                except:
                    continue
            
            if apply_button:
                break
        
        if not apply_button:
            try:
                print("❌ IPO not found. Available IPOs:")
                ipo_elements = driver.find_elements(By.XPATH, "//button[contains(@class,'btn-issue') or contains(text(),'Apply')]/ancestor::div[contains(@class,'row') or contains(@class,'company')]")
                for i, element in enumerate(ipo_elements[:5]):  # Show first 5
                    print(f"  {i+1}. {element.text[:100]}...")
            except:
                pass
            raise Exception(f"IPO '{ipo_name}' not found or Apply button not available")
        
        # Scroll to button and click
        driver.execute_script("arguments[0].scrollIntoView(true);", apply_button)
        time.sleep(1)
        
        if ipo_number:
            target_url = f"https://meroshare.cdsc.com.np/#/asba/apply/{ipo_number}"
            print(f"🔗 Navigating to: {target_url}")
            driver.get(target_url)
            time.sleep(3)
            print(f"✅ Successfully navigated to IPO application page")
        else:
            # Fallback to clicking the button if no number found
            apply_button.click()
            time.sleep(2)
            print(f"✅ Clicked Apply button for IPO: {ipo_name}")
        
    except Exception as e:
        raise Exception(f"Failed to find and apply for IPO '{ipo_name}': {e}")


def fill_ipo_form(driver, acc):
    """Auto-fill IPO application form with enhanced error handling"""
    try:
        print("🔄 Waiting for IPO application form to load...")
        
        # Wait for the form container to be present first
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//form | //div[contains(@class,'form')] | //div[contains(@class,'application')]"))
        )
        time.sleep(3)  # Additional wait for dynamic content
        
        bank_dropdown = None
        bank_selectors = [
            (By.ID, "bank"),
            (By.NAME, "bank"),
            (By.XPATH, "//select[contains(@id,'bank') or contains(@name,'bank')]"),
            (By.XPATH, "//select[contains(@class,'bank')]"),
            (By.XPATH, "//label[contains(text(),'Bank')]/following-sibling::select"),
            (By.XPATH, "//label[contains(text(),'Bank')]/parent::*/select")
        ]
        
        for selector_type, selector_value in bank_selectors:
            try:
                print(f"🔍 Trying bank selector: {selector_type} = {selector_value}")
                bank_dropdown = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((selector_type, selector_value))
                )
                print(f"✅ Found bank dropdown using: {selector_type} = {selector_value}")
                break
            except:
                continue
        
        if not bank_dropdown:
            print("🔍 Bank dropdown not found with standard selectors, searching all select elements...")
            select_elements = driver.find_elements(By.TAG_NAME, "select")
            for i, select_elem in enumerate(select_elements):
                try:
                    # Check if this select contains bank-related options
                    options = select_elem.find_elements(By.TAG_NAME, "option")
                    option_texts = [opt.text.lower() for opt in options if opt.text.strip()]
                    
                    # Look for bank-related keywords in options
                    bank_keywords = ['bank', 'nabil', 'nic', 'everest', 'standard', 'himalayan', 'nepal investment']
                    if any(keyword in ' '.join(option_texts) for keyword in bank_keywords):
                        bank_dropdown = select_elem
                        print(f"✅ Found bank dropdown by content analysis (select #{i})")
                        break
                except:
                    continue
        
        if not bank_dropdown:
            raise Exception("Bank dropdown not found with any selector method")
        
        bank_dropdown.click()
        time.sleep(1)
        
        # Get bank name from env and select it
        bank_name = config("BANK_NAME", default="")
        if bank_name:
            bank_selected = False
            bank_option_selectors = [
                f"//option[contains(text(),'{bank_name}')]",
                f"//option[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'{bank_name.lower()}')]",
                f"//select[@id='bank']//option[contains(text(),'{bank_name}')]",
                f"//select//option[contains(text(),'{bank_name}')]"
            ]
            
            for selector in bank_option_selectors:
                try:
                    bank_option = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    bank_option.click()
                    print(f"✅ Selected bank: {bank_name}")
                    bank_selected = True
                    break
                except:
                    continue
            
            if not bank_selected:
                try:
                    first_bank_option = bank_dropdown.find_elements(By.TAG_NAME, "option")[1]  # Skip first empty option
                    first_bank_option.click()
                    print(f"⚠️ Bank '{bank_name}' not found, selected first available bank: {first_bank_option.text}")
                except:
                    print(f"❌ Could not select any bank option")
        
        time.sleep(1)
        
        account_dropdown = None
        account_selectors = [
            (By.ID, "accountNumber"),
            (By.NAME, "accountNumber"),
            (By.XPATH, "//select[contains(@id,'account') or contains(@name,'account')]"),
            (By.XPATH, "//label[contains(text(),'Account')]/following-sibling::select"),
            (By.XPATH, "//label[contains(text(),'Account')]/parent::*/select")
        ]
        
        for selector_type, selector_value in account_selectors:
            try:
                account_dropdown = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((selector_type, selector_value))
                )
                print(f"✅ Found account dropdown using: {selector_type} = {selector_value}")
                break
            except:
                continue
        
        if account_dropdown:
            account_dropdown.click()
            time.sleep(1)
            
            try:
                account_options = account_dropdown.find_elements(By.TAG_NAME, "option")
                if len(account_options) > 1:
                    account_options[1].click()  # Select first non-empty option
                    print("✅ Selected first available account number")
                else:
                    print("⚠️ No account options found")
            except Exception as e:
                print(f"⚠️ Could not select account: {e}")
        else:
            print("⚠️ Account dropdown not found")
        
        time.sleep(1)
        
        if acc.get("lot"):
            kitta_field = None
            kitta_selectors = [
                (By.ID, "appliedKitta"),
                (By.NAME, "appliedKitta"),
                (By.XPATH, "//input[contains(@id,'kitta') or contains(@name,'kitta')]"),
                (By.XPATH, "//input[@type='number']"),
                (By.XPATH, "//label[contains(text(),'Kitta') or contains(text(),'Unit')]/following-sibling::input"),
                (By.XPATH, "//label[contains(text(),'Kitta') or contains(text(),'Unit')]/parent::*/input")
            ]
            
            for selector_type, selector_value in kitta_selectors:
                try:
                    kitta_field = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    break
                except:
                    continue
            
            if kitta_field:
                kitta_field.clear()
                kitta_field.send_keys(acc["lot"])
                
                # Trigger change event for amount calculation
                driver.execute_script("""
                    arguments[0].dispatchEvent(new Event('input', { bubbles: true })); 
                    arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                """, kitta_field)
                
                print(f"✅ Entered applied kitta: {acc['lot']}")
            else:
                print("⚠️ Kitta field not found")
        
        if acc.get("crn"):
            crn_field = None
            crn_selectors = [
                (By.ID, "crn"),
                (By.NAME, "crn"),
                (By.XPATH, "//input[contains(@id,'crn') or contains(@name,'crn')]"),
                (By.XPATH, "//label[contains(text(),'CRN')]/following-sibling::input"),
                (By.XPATH, "//label[contains(text(),'CRN')]/parent::*/input")
            ]
            
            for selector_type, selector_value in crn_selectors:
                try:
                    crn_field = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    break
                except:
                    continue
            
            if crn_field:
                crn_field.clear()
                crn_field.send_keys(acc["crn"])
                print(f"✅ Entered CRN: {acc['crn']}")
            else:
                print("⚠️ CRN field not found")
        
        declaration_checkbox = None
        declaration_selectors = [
            (By.ID, "declaration"),
            (By.NAME, "declaration"),
            (By.XPATH, "//input[@type='checkbox'][contains(@id,'declaration') or contains(@name,'declaration')]"),
            (By.XPATH, "//input[@type='checkbox']"),
            (By.XPATH, "//label[contains(text(),'declaration') or contains(text(),'Declaration')]/input[@type='checkbox']"),
            (By.XPATH, "//label[contains(text(),'declaration') or contains(text(),'Declaration')]/preceding-sibling::input[@type='checkbox']")
        ]
        
        for selector_type, selector_value in declaration_selectors:
            try:
                declaration_checkbox = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((selector_type, selector_value))
                )
                break
            except:
                continue
        
        if declaration_checkbox and not declaration_checkbox.is_selected():
            declaration_checkbox.click()
            print("✅ Ticked declaration checkbox")
        elif declaration_checkbox:
            print("✅ Declaration checkbox already selected")
        else:
            print("⚠️ Declaration checkbox not found")
        
        time.sleep(1)
        
        proceed_button = None
        proceed_selectors = [
            "//button[contains(text(),'Proceed')]",
            "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'proceed')]",
            "//input[@type='submit'][contains(@value,'Proceed')]",
            "//button[@type='submit']",
            "//button[contains(@class,'btn-primary')]"
        ]
        
        for selector in proceed_selectors:
            try:
                proceed_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                break
            except:
                continue
        
        if proceed_button:
            proceed_button.click()
            time.sleep(3)
            print("✅ Clicked Proceed button")
        else:
            print("⚠️ Proceed button not found")
        
    except Exception as e:
        print(f"❌ Error in fill_ipo_form: {e}")
        try:
            print(f"Current URL: {driver.current_url}")
            print(f"Page title: {driver.title}")
            # Take screenshot of current state for debugging
            driver.save_screenshot("error_screenshot.png")
            print("📸 Screenshot saved as error_screenshot.png")
        except:
            pass
        raise Exception(f"Failed to fill IPO form: {e}")


def enter_pin_and_submit(driver, acc):
    """Enter 4-digit PIN and click Apply button to complete application"""
    try:
        if not acc.get("pin"):
            raise Exception("PIN not found in account configuration")
        
        print("🔄 Waiting for PIN entry page...")
        time.sleep(2)
        
        pin_field = None
        pin_selectors = [
            (By.ID, "pin"),
            (By.NAME, "pin"),
            (By.XPATH, "//input[contains(@id,'pin') or contains(@name,'pin')]"),
            (By.XPATH, "//input[@type='password']"),
            (By.XPATH, "//input[@maxlength='4']"),
            (By.XPATH, "//label[contains(text(),'PIN')]/following-sibling::input"),
            (By.XPATH, "//label[contains(text(),'PIN')]/parent::*/input")
        ]
        
        for selector_type, selector_value in pin_selectors:
            try:
                pin_field = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((selector_type, selector_value))
                )
                print(f"✅ Found PIN field using: {selector_type} = {selector_value}")
                break
            except:
                continue
        
        if not pin_field:
            raise Exception("PIN field not found with any selector method")
        
        pin_field.clear()
        pin_field.send_keys(acc["pin"])
        print(f"✅ Entered PIN")
        
        print("🔄 Waiting for Apply button to become enabled...")
        time.sleep(3)  # Wait for PIN validation
        
        apply_button = None
        
        # Wait for any button to appear first
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "button"))
            )
        except:
            pass
        
        # More specific selectors based on the actual HTML structure
        apply_selectors = [
            # Most specific - exact class combination from the image
            "//button[contains(@class,'btn') and contains(@class,'btn-gap') and contains(@class,'btn-primary')]",
            "//button[contains(@class,'btn-gap') and contains(@class,'btn-primary')]",
            "//button[contains(@class,'btn-primary') and @type='submit']",
            
            # Alternative specific selectors
            "//button[@type='submit' and contains(@class,'btn')]",
            "//button[contains(@class,'btn-primary')]",
            "//button[@type='submit']",
            
            # Text-based selectors
            "//button[contains(text(),'Apply')]",
            "//button[normalize-space(text())='Apply']",
            "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'apply')]",
            
            # Input submit buttons
            "//input[@type='submit' and contains(@value,'Apply')]",
            "//input[@type='submit']",
            
            # Broader selectors
            "//form//button[last()]",
            "//div[contains(@class,'modal')]//button[contains(@class,'btn-primary')]",
            "//div[contains(@class,'footer')]//button[not(contains(@class,'btn-default'))]"
        ]
        
        for i, selector in enumerate(apply_selectors):
            try:
                print(f"🔍 Trying Apply button selector {i+1}: {selector}")
                
                # Wait for button to be present
                buttons = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.XPATH, selector))
                )
                
                for button in buttons:
                    try:
                        # Check if button is not disabled
                        if button.get_attribute('disabled') is None:
                            # Additional check - make sure it's visible and clickable
                            if button.is_displayed() and button.is_enabled():
                                apply_button = button
                                print(f"✅ Found enabled Apply button using selector {i+1}")
                                break
                        else:
                            print(f"⚠️ Button found but disabled, waiting for it to be enabled...")
                            # Wait up to 10 seconds for button to become enabled
                            for wait_count in range(10):
                                time.sleep(1)
                                if button.get_attribute('disabled') is None:
                                    apply_button = button
                                    print(f"✅ Button enabled after {wait_count + 1} seconds")
                                    break
                            if apply_button:
                                break
                    except Exception as btn_error:
                        print(f"⚠️ Error checking button: {btn_error}")
                        continue
                
                if apply_button:
                    break
                    
            except Exception as e:
                print(f"⚠️ Selector {i+1} failed: {str(e)[:100]}...")
                continue
        
        # If still no button found, do comprehensive debugging
        if not apply_button:
            print("🔍 Apply button not found. Debugging all available buttons...")
            try:
                all_buttons = driver.find_elements(By.TAG_NAME, "button")
                all_inputs = driver.find_elements(By.XPATH, "//input[@type='submit' or @type='button']")
                
                print(f"📋 Found {len(all_buttons)} button elements and {len(all_inputs)} input elements:")
                
                # Check all buttons
                for i, btn in enumerate(all_buttons):
                    try:
                        text = btn.text.strip()
                        classes = btn.get_attribute('class') or ''
                        btn_type = btn.get_attribute('type') or ''
                        disabled = btn.get_attribute('disabled')
                        visible = btn.is_displayed()
                        enabled = btn.is_enabled()
                        
                        print(f"  Button {i+1}: text='{text}', class='{classes}', type='{btn_type}', disabled={disabled}, visible={visible}, enabled={enabled}")
                        
                        # Try to find a suitable button
                        if (disabled is None and visible and enabled and 
                            (text.lower() in ['apply', 'submit', 'confirm', 'continue'] or 
                             'btn-primary' in classes or 'btn-issue' in classes)):
                            print(f"🎯 Using button {i+1} as Apply button")
                            apply_button = btn
                            break
                            
                    except Exception as e:
                        print(f"  Button {i+1}: Error - {e}")
                
                # Check input elements if no button found
                if not apply_button:
                    for i, inp in enumerate(all_inputs):
                        try:
                            value = inp.get_attribute('value') or ''
                            classes = inp.get_attribute('class') or ''
                            disabled = inp.get_attribute('disabled')
                            visible = inp.is_displayed()
                            enabled = inp.is_enabled()
                            
                            print(f"  Input {i+1}: value='{value}', class='{classes}', disabled={disabled}, visible={visible}, enabled={enabled}")
                            
                            if (disabled is None and visible and enabled and 
                                value.lower() in ['apply', 'submit', 'confirm']):
                                print(f"🎯 Using input {i+1} as Apply button")
                                apply_button = inp
                                break
                                
                        except Exception as e:
                            print(f"  Input {i+1}: Error - {e}")
                            
            except Exception as debug_error:
                print(f"❌ Error during debugging: {debug_error}")
        
        if not apply_button:
            # Take screenshot for debugging
            try:
                driver.save_screenshot("apply_button_not_found.png")
                print("📸 Screenshot saved as apply_button_not_found.png")
            except:
                pass
            raise Exception("Apply button not found after comprehensive search")
        
        # Click the Apply button
        try:
            # Scroll to button first
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", apply_button)
            time.sleep(1)
            
            # Try regular click
            apply_button.click()
            print("✅ Successfully clicked Apply button")
            
        except Exception as click_error:
            print(f"⚠️ Regular click failed: {click_error}")
            try:
                # Try JavaScript click as fallback
                driver.execute_script("arguments[0].click();", apply_button)
                print("✅ Successfully clicked Apply button using JavaScript")
            except Exception as js_error:
                raise Exception(f"Both regular and JavaScript clicks failed: {click_error}, {js_error}")
        
        # Wait for completion and check for success
        time.sleep(5)
        print("✅ Apply button clicked - waiting for confirmation...")
        
        # Check for success indicators
        try:
            success_indicators = [
                "//div[contains(text(),'success') or contains(text(),'Success')]",
                "//div[contains(text(),'submitted') or contains(text(),'Submitted')]",
                "//div[contains(text(),'applied') or contains(text(),'Applied')]",
                "//div[contains(text(),'complete') or contains(text(),'Complete')]",
                "//div[contains(text(),'successful') or contains(text(),'Successful')]",
                "//*[contains(@class,'success') or contains(@class,'alert-success')]",
                "//*[contains(@class,'confirmation')]"
            ]
            
            for indicator in success_indicators:
                try:
                    success_element = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, indicator))
                    )
                    print(f"🎉 Success confirmation: {success_element.text[:100]}")
                    break
                except:
                    continue
            else:
                print("⚠️ No explicit success message found, but Apply button was clicked successfully")
                
        except Exception as e:
            print(f"⚠️ Error checking success: {e}")
        
        print("🎉 IPO application process completed!")
        
    except Exception as e:
        print(f"❌ Error in enter_pin_and_submit: {e}")
        try:
            print(f"Current URL: {driver.current_url}")
            driver.save_screenshot("pin_submit_error.png")
            print("📸 Error screenshot saved as pin_submit_error.png")
        except:
            pass
        raise Exception(f"Failed to complete PIN submission: {e}")


def apply_ipo_for_account(driver, acc):
    """Complete IPO application process for one account"""
    try:
        # Navigate to My ASBA
        navigate_to_asba(driver)
        
        # Find specific IPO and Apply
        select_ipo_and_apply(driver)
        
        # Fill the IPO form
        fill_ipo_form(driver, acc)
        
        # Enter PIN and submit
        enter_pin_and_submit(driver, acc)
        
        print(f"🎉 IPO application completed for {acc['name']}")
        
    except Exception as e:
        print(f"❌ IPO application failed for {acc['name']}: {e}")
        raise


def apply_ipo_for_all():
    """Main function"""
    accounts = load_accounts()

    if not accounts:
        print("❌ No accounts found in .env")
        return

    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=options)

    print(f"🎉 Chrome opened. {len(accounts)} accounts to process.")

    for i, acc in enumerate(accounts, 1):
        print(f"\n=== Processing {acc['name']} ({i}/{len(accounts)}) ===")
        try:
            print(f"🔑 Starting login process for {acc['name']}...")
            login(driver, acc)
            print(f"✅ Login process completed for {acc['name']}")
            
            print("🚀 Starting IPO application process...")
            apply_ipo_for_account(driver, acc)
            
        except Exception as e:
            print(f"❌ Error processing {acc['name']}: {e}")
            import traceback
            print(f"Full error traceback: {traceback.format_exc()}")
            try:
                print(f"Current URL when error occurred: {driver.current_url}")
                print(f"Page title: {driver.title}")
            except:
                pass
            # Continue with next account
            continue

    driver.quit()


if __name__ == "__main__":
    apply_ipo_for_all()