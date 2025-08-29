import asyncio
import os
import json
import time
import random
import logging
import requests
from datetime import datetime
from functools import wraps
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import zendriver as zd
from session_manager import SessionManager
from database import DatabaseManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('zendriver_api.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Environment variables
ZENDRIVER_URL = os.getenv('ZENDRIVER_URL', 'http://localhost:4444')
CALLBACK_TIMEOUT = int(os.getenv('CALLBACK_TIMEOUT', '360'))
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
JOB_TIMEOUT = int(os.getenv('JOB_TIMEOUT', '300'))
BASE_URL = os.getenv('BASE_URL', 'https://immensely-ace-jaguar.ngrok-free.app')

# Initialize Flask app
app = Flask(__name__)
CORS(app)

logger = logging.getLogger(__name__)

# Initialize database manager
db = DatabaseManager()

# Session management configuration
SESSION_TIMEOUT = 30 * 60  # 30 minutes
MAX_SESSIONS = 100  # Maximum number of concurrent sessions

# Shared Chrome profile for persistent cookies (cross-platform path)
import platform
if platform.system() == "Windows":
    SHARED_PROFILE_DIR = os.path.join(os.path.expanduser("~"), "zendriver_profile")
else:
    SHARED_PROFILE_DIR = "./shared_chrome_profile"

class ZendriverSession:
    """Zendriver session management class - Google Flow automation"""
    
    def __init__(self, job_id, user_id):
        self.job_id = job_id
        self.user_id = user_id
        self.browser = None
        self.page = None
        self.status = "initializing"
        self.session_manager = SessionManager()
        self.logger = logging.getLogger(f"ZendriverSession_{job_id}")
        
    async def create_session(self):
        """Create Zendriver session with Chrome options"""
        try:
            self.logger.info(f"Creating Zendriver session for job {self.job_id}")
            
            # Ensure shared profile directory exists
            os.makedirs(SHARED_PROFILE_DIR, exist_ok=True)
            
            # Chrome options (user-data-dir handled by zendriver parameter)
            chrome_args = [
                "--no-first-run",
                "--no-service-autorun", 
                "--no-default-browser-check",
                "--homepage=about:blank",
                "--no-pings",
                "--password-store=basic",
                "--disable-infobars",
                "--disable-breakpad",
                "--disable-component-update",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-background-networking",
                "--disable-dev-shm-usage",
                "--disable-features=IsolateOrigins,DisableLoadExtensionCommandLineSwitch,site-per-process",
                "--disable-session-crashed-bubble",
                "--disable-search-engine-choice-screen",
                "--disable-features=ProfilePicker"  # Skip profile picker
            ]
            
            # Create zendriver config with persistent profile
            self.browser = await zd.start(
                user_data_dir=SHARED_PROFILE_DIR,
                browser_args=chrome_args
            )
            self.page = await self.browser.get("https://accounts.google.com")
            
            # Apply stealth scripts
            await self.apply_stealth_scripts()
            await asyncio.sleep(3)
            
            self.status = "ready"
            self.logger.info(f"Zendriver session created successfully for job {self.job_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create Zendriver session for job {self.job_id}: {e}")
            self.status = "failed"
            return False
        
    async def apply_stealth_scripts(self):
        """Apply stealth scripts to avoid detection"""
        try:
            logger.info("Applying stealth scripts...")
            
            # Hide WebDriver property
            await self.page.evaluate("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            # Mock Chrome runtime
            await self.page.evaluate("""
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
            """)
            
            logger.info("Stealth scripts applied successfully")
            
        except Exception as e:
            logger.error(f"Stealth script error: {e}")
    
    async def human_like_typing(self, element, text):
        """Human-like typing simulation"""
        try:
            for char in text:
                await element.send_keys(char)
                await asyncio.sleep(random.uniform(0.05, 0.15))
        except Exception as e:
            logger.error(f"Typing error: {e}")
    
    async def login_with_credentials(self, email: str, password: str):
        """Login with email and password"""
        try:
            self.logger.info("Starting login process...")
            
            # Ensure we're on the login page
            await self.page.get("https://accounts.google.com/signin")
            await asyncio.sleep(3)
            
            # Apply stealth scripts
            await self.apply_stealth_scripts()
            await asyncio.sleep(3)
            
            # Log current page state for debugging
            current_url = await self.page.evaluate("window.location.href")
            page_title = await self.page.evaluate("document.title")
            self.logger.info(f"Login page URL: {current_url}")
            self.logger.info(f"Login page title: {page_title}")
            
            # Find and fill email field
            email_selectors = [
                'input[name="identifier"]',
                'input[type="email"]',
                '#identifierId',
                'input[autocomplete="username"]'
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    email_field = await self.page.find(selector)
                    if email_field:
                        break
                except:
                    continue
            
            if not email_field:
                raise Exception("Email field not found")
            
            # Type email
            logger.info("Typing email...")
            await self.human_like_typing(email_field, email)
            await asyncio.sleep(2)
            
            # Find and click Next button
            next_selectors = [
                '#identifierNext',
                'button[data-idom-e2e="identifier-next"]',
                'button:contains("Next")',
                'button:contains("İleri")'
            ]
            
            next_button = None
            for selector in next_selectors:
                try:
                    next_button = await self.page.find(selector)
                    if next_button:
                        break
                except:
                    continue
            
            if not next_button:
                raise Exception("Next button not found")
            
            await next_button.click()
            logger.info("Clicked Next button")
            await asyncio.sleep(3)
            
            # Find and fill password field
            password_selectors = [
                'input[name="Passwd"]',
                'input[type="password"]',
                'input[autocomplete="current-password"]'
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = await self.page.find(selector)
                    if password_field:
                        break
                except:
                    continue
            
            if not password_field:
                raise Exception("Password field not found")
            
            # Type password
            logger.info("Typing password...")
            await self.human_like_typing(password_field, password)
            await asyncio.sleep(2)
            
            # Find and click Password Next button
            password_next_selectors = [
                '#passwordNext',
                'button[data-idom-e2e="password-next"]',
                'button:contains("Next")',
                'button:contains("İleri")'
            ]
            
            password_next = None
            for selector in password_next_selectors:
                try:
                    password_next = await self.page.find(selector)
                    if password_next:
                        break
                except:
                    continue
            
            if not password_next:
                raise Exception("Password Next button not found")
            
            await password_next.click()
            logger.info("Clicked Password Next button")
            await asyncio.sleep(5)
            
            # Check login result
            try:
                current_url = await self.page.evaluate("window.location.href")
            except:
                current_url = self.page.url
            
            logger.info(f"Login result URL: {current_url}")
            
            # Handle browser crash
            if "about:blank" in current_url or not current_url or current_url == "":
                logger.warning("Browser crash detected, reloading page...")
                await self.page.get("https://myaccount.google.com")
                await asyncio.sleep(3)
                try:
                    current_url = await self.page.evaluate("window.location.href")
                except:
                    current_url = self.page.url
            
            # Check login status
            if "myaccount.google.com" in current_url or "gmail.com" in current_url:
                logger.info("Login successful!")
                return True
            elif "accounts.google.com" in current_url:
                # Still on login page, might need to wait more
                logger.info("Still on login page, waiting...")
                await asyncio.sleep(5)
                try:
                    current_url = await self.page.evaluate("window.location.href")
                except:
                    current_url = self.page.url
                
                if "myaccount.google.com" in current_url or "gmail.com" in current_url:
                    logger.info("Login successful after waiting!")
                    return True
                else:
                    logger.warning(f"Login status unclear after waiting: {current_url}")
                    return False
            else:
                logger.warning(f"Login status unclear: {current_url}")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    async def navigate_to_flow(self):
        """Navigate to Google Flow"""
        try:
            logger.info("Navigating to Google Flow...")
            await self.page.get("https://labs.google/fx/tools/flow")
            await asyncio.sleep(3)
            logger.info("Successfully navigated to Google Flow")
            return True
        except Exception as e:
            logger.error(f"Navigation to Flow error: {e}")
            return False
    
    async def take_screenshot(self, filename=None):
        """Take screenshot"""
        try:
            if not filename:
                filename = f"screenshot_{self.job_id}_{int(time.time())}.png"
            
            await self.page.save_screenshot(filename)
            logger.info(f"Screenshot saved: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return None
    

    async def is_logged_in(self):
        """Check if user is still logged in to Google via cookies"""
        try:
            self.logger.info("Checking login status via cookies...")
            
            # Try to access a protected Google service that requires login
            await self.page.get("https://accounts.google.com/ManageAccount")
            await asyncio.sleep(4)
            
            current_url = await self.page.evaluate("window.location.href")
            self.logger.info(f"Cookie check result URL: {current_url}")
            
            # If we're redirected to signin, we're not logged in
            if "accounts.google.com/signin" in current_url or "accounts.google.com/v3/signin" in current_url:
                self.logger.info("Redirected to signin - not logged in")
                return False
            elif "myaccount.google.com" in current_url or "accounts.google.com/ManageAccount" in current_url:
                self.logger.info("User is logged in via saved cookies!")
                return True
            else:
                self.logger.warning(f"Unexpected URL during cookie check: {current_url}")
                return False
            
        except Exception as e:
            self.logger.error(f"Login check failed: {e}")
            return False

    async def smart_login(self, email, password):
        """Smart login - check cookies first, then login if needed"""
        try:
            self.logger.info("Starting smart login process...")
            
            # First check if already logged in via cookies
            if await self.is_logged_in():
                self.logger.info("Already logged in via cookies - skipping login!")
                return True
            
            # Not logged in, proceed with normal login
            self.logger.info("Not logged in, proceeding with credential login...")
            return await self.login_with_credentials(email, password)
            
        except Exception as e:
            self.logger.error(f"Smart login failed: {e}")
            return False


    async def validate_project_access(self, project_id):
        """Check if project is still accessible"""
        try:
            self.logger.info(f"Validating access to project: {project_id}")
            
            project_url = f"https://labs.google/fx/tools/flow/project/{project_id}"
            await self.page.get(project_url)
            await asyncio.sleep(3)
            
            current_url = await self.page.evaluate("window.location.href")
            is_accessible = project_id in current_url
            
            if is_accessible:
                self.logger.info(f"Project {project_id} is accessible")
            else:
                self.logger.warning(f"Project {project_id} not accessible, current URL: {current_url}")
                
            return is_accessible
            
        except Exception as e:
            self.logger.error(f"Project validation failed: {e}")
            return False

    async def close_session(self):
        """Close Zendriver session"""
        try:
            if self.browser:
                await self.browser.stop()
                self.logger.info(f"Zendriver session closed for job {self.job_id}")
        except Exception as e:
            self.logger.error(f"Error closing session: {e}")
    
    async def handle_onboarding(self):
        """Handle complete onboarding flow - Next button and Policy scroll"""
        try:
            self.logger.info("Starting comprehensive onboarding flow...")
            
            # Step 1: Look for initial popup with "Next" button
            await asyncio.sleep(3)  # Wait for popup to appear
            
            next_button_selectors = [
                'button:contains("Next")',
                'button:contains("İleri")',
                'button[data-testid="next-button"]',
                'button[aria-label*="Next"]',
                'button[aria-label*="İleri"]'
            ]
            
            # Try to find and click Next button
            next_clicked = False
            for selector in next_button_selectors:
                try:
                    next_button = await self.page.find(selector, timeout=2000)  # 2 second timeout
                    if next_button:
                        self.logger.info(f"Next button found: {selector}")
                        await next_button.click()
                        self.logger.info("Next button clicked")
                        await asyncio.sleep(3)  # Wait for next screen
                        next_clicked = True
                        break
                except Exception as e:
                    continue
            
            if not next_clicked:
                self.logger.info("Next button not found - might not be first onboarding step")
            
            # Step 2: Handle Policy page - scroll down and click Continue
            policy_continue_selectors = [
                'button:contains("Continue")',
                'button:contains("Devam")',
                'button[data-testid="continue-button"]',
                'button[aria-label*="Continue"]',
                'button[aria-label*="Devam"]'
            ]
            
            # First, try to scroll down to activate Continue button
            try:
                self.logger.info("Scrolling down to activate Continue button...")
                # Scroll to bottom of the page multiple times to ensure we reach the end
                for i in range(5):
                    await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                    await asyncio.sleep(0.5)
                    
                # Also try scrolling specific policy container if exists
                await self.page.evaluate("""
                    // Try to find and scroll policy container
                    const containers = document.querySelectorAll('div[role="dialog"], .policy-container, .terms-container');
                    containers.forEach(container => {
                        container.scrollTop = container.scrollHeight;
                    });
                """)
                await asyncio.sleep(2)
                
            except Exception as scroll_error:
                self.logger.warning(f"Scrolling error: {scroll_error}")
            
            # Try to find and click Continue button
            continue_clicked = False
            for selector in policy_continue_selectors:
                try:
                    continue_button = await self.page.find(selector, timeout=2000)  # 2 second timeout
                    if continue_button:
                        # Check if button is enabled
                        is_disabled = await continue_button.get("disabled")
                        if is_disabled:
                            self.logger.warning(f"Continue button found but disabled: {selector}")
                            # Try scrolling more
                            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                            await asyncio.sleep(1)
                            continue
                        
                        self.logger.info(f"Continue button found and enabled: {selector}")
                        await continue_button.click()
                        self.logger.info("Continue button clicked")
                        await asyncio.sleep(3)  # Wait for next screen
                        continue_clicked = True
                        break
                except Exception as e:
                    continue
            
            if not continue_clicked:
                self.logger.info("Continue button not found or not clickable")
            
            # Step 3: Legacy onboarding buttons (fallback)
            legacy_selectors = [
                'button:contains("Başlayın")',  # Turkish
                'button:contains("Get Started")',  # English
                'button:contains("Başla")',  # Alternative Turkish
                '[data-testid="get-started-button"]',
                '.get-started-button',
                'button[aria-label*="Başlayın"]',
                'button[aria-label*="Get Started"]'
            ]
            
            for selector in legacy_selectors:
                try:
                    button = await self.page.find(selector, timeout=1000)  # 1 second timeout
                    if button:
                        self.logger.info(f"Legacy onboarding button found: {selector}")
                        await button.click()
                        self.logger.info("Legacy onboarding button clicked")
                        await asyncio.sleep(2)
                        break
                except Exception as e:
                    continue
            
            self.logger.info("Onboarding flow completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Onboarding flow error: {e}")
            return False
    
    async def create_new_project(self):
        """Create new project in Google Flow"""
        try:
            self.logger.info("Creating new project...")
            
            # Navigate to Google Flow
            await self.page.get("https://labs.google/fx/tools/flow")
            await asyncio.sleep(10)  # Wait for page load
            
            # Check if first login and handle onboarding
            if self.session_manager.is_first_login():
                self.logger.info("First login detected - checking onboarding...")
                onboarding_handled = await self.handle_onboarding()
                
                if onboarding_handled:
                    # Mark onboarding as completed
                    self.session_manager.mark_onboarding_completed()
                    self.logger.info("Onboarding marked as completed")
            else:
                self.logger.info("This account has logged in before - skipping onboarding")
            
            # Find and click "New project" button
            self.logger.info("Looking for New project button (best_match)...")
            
            new_project_button = await self.page.find(text="New project", best_match=True)
            
            if not new_project_button:
                # Fallback selectors
                fallback_selectors = [
                    'button:contains("New project")',
                    'button:contains("Yeni proje")',
                    '[data-testid="new-project-button"]',
                    '.new-project-button'
                ]
                
                for selector in fallback_selectors:
                    try:
                        new_project_button = await self.page.find(selector)
                        if new_project_button:
                            break
                    except:
                        continue
            
            if not new_project_button:
                self.logger.error("New project button not found!")
                return False
            
            # Click new project button
            await new_project_button.click()
            self.logger.info("New project button clicked")
            await asyncio.sleep(10)  # Wait for project creation
            
            # Check if new project URL is created
            try:
                current_url = await self.page.evaluate("window.location.href")
            except:
                current_url = self.page.url
            self.logger.info(f"Current URL: {current_url}")
            
            if "/project/" in current_url:
                # Extract project ID from URL
                project_id = current_url.split("/project/")[-1].split("?")[0]
                self.logger.info(f"New project URL detected! Project ID: {project_id}")
                self.logger.info("New project created and opened successfully")
                return project_id
            else:
                self.logger.error("New project URL not detected!")
                return False
                
        except Exception as e:
            self.logger.error(f"Create new project error: {e}")
            return False
    
    async def navigate_to_existing_project(self, project_id):
        """Navigate to existing project by project ID"""
        try:
            self.logger.info(f"Navigating to existing project: {project_id}")
            
            # Navigate directly to the project URL
            project_url = f"https://labs.google/fx/tools/flow/project/{project_id}"
            await self.page.get(project_url)
            await asyncio.sleep(5)  # Wait for page load
            
            # Check if we're on the correct project page
            try:
                current_url = await self.page.evaluate("window.location.href")
            except:
                current_url = self.page.url
            
            if project_id in current_url:
                self.logger.info(f"Successfully navigated to project: {project_id}")
                return True
            else:
                self.logger.error(f"Failed to navigate to project: {project_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Navigate to existing project error: {e}")
            return False
    
    async def create_video_from_text(self, prompt_text):
        """Create video from text prompt"""
        try:
            self.logger.info(f"Creating video: {prompt_text}")
            
            # Find text input field
            self.logger.info("Looking for text input field...")
            
            text_input_selectors = [
                'textarea[placeholder*="Generate a video with text"]',
                'textarea[placeholder*="Metin içeren bir video üretin"]',
                '[role="textbox"][aria-label*="Generate a video with text"]',
                'textarea[aria-label*="Generate a video with text"]',
                'textarea[placeholder*="Enter your prompt"]',
                'textarea[placeholder*="Prompt"]',
                'input[placeholder*="Enter your prompt"]',
                'input[placeholder*="Prompt"]',
                'textarea',
                'input[type="text"]'
            ]
            
            text_input = None
            for selector in text_input_selectors:
                try:
                    self.logger.info(f"Looking for text input: {selector}")
                    text_input = await self.page.find(selector)
                    if text_input:
                        self.logger.info(f"Text input found: {selector}")
                        break
                    else:
                        self.logger.warning(f"Selector found but element returned empty: {selector}")
                except Exception as e:
                    self.logger.error(f"Selector error: {selector} - {e}")
                    continue
            
            if not text_input:
                self.logger.error("Text input field not found!")
                return False
            
            # Type text - using Zendriver send_keys()
            try:
                await text_input.send_keys(prompt_text)
                await asyncio.sleep(2)
                self.logger.info("Text typed with send_keys()")
            except Exception as e:
                self.logger.error(f"send_keys() error: {e}")
                # Fallback: JavaScript
                try:
                    result = await self.page.evaluate(f"""
                        (() => {{
                            const textarea = document.querySelector('{text_input_selectors[0]}');
                            if (textarea) {{
                                textarea.value = '{prompt_text}';
                                textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                return textarea.value;
                            }}
                            return null;
                        }})();
                    """)
                    
                    if result == prompt_text:
                        self.logger.info("Text typed with JavaScript (fallback)")
                    else:
                        self.logger.warning(f"JavaScript typing result: {result}")
                        
                except Exception as fallback_error:
                    self.logger.error(f"JavaScript fallback error: {fallback_error}")
                    return False
            
            # Find and click Generate button
            self.logger.info("Looking for Generate button...")
            
            # Both English and Turkish button texts
            generate_button_texts = [
                "Generate",  # English
                "Oluştur",   # Turkish
                "Generate video",  # English long
                "Video oluştur",   # Turkish long
                "Create",    # English alternative
                "Oluştur video",   # Turkish alternative
                "Generate with text",  # English detailed
                "Metin ile oluştur"    # Turkish detailed
            ]
            
            generate_button = None
            for button_text in generate_button_texts:
                try:
                    self.logger.info(f"Looking for Generate button: '{button_text}'")
                    generate_button = await self.page.find(text=button_text, best_match=True)
                    if generate_button and generate_button is not None:
                        self.logger.info(f"Generate button found: '{button_text}'")
                        break
                    else:
                        self.logger.info(f"Generate button not found: '{button_text}'")
                except Exception as e:
                    self.logger.info(f"Generate button search error: '{button_text}' - {e}")
                    continue
            
            if not generate_button:
                self.logger.error("Generate button not found!")
                return False
            
            # Click button - Zendriver native click()
            try:
                # Check if button is disabled
                is_disabled = await generate_button.get("disabled")
                if is_disabled:
                    self.logger.warning("Generate button is disabled!")
                    self.logger.info("This is normal - insufficient credits or text")
                    return True
                
                await generate_button.click()
                self.logger.info("Generate button clicked")
                await asyncio.sleep(5)  # Wait for process
            except Exception as e:
                self.logger.error(f"Generate button click error: {e}")
                # Fallback: JavaScript click
                try:
                    result = await self.page.evaluate(f"""
                        (() => {{
                            const buttons = document.querySelectorAll('button');
                            for (let button of buttons) {{
                                if (button.textContent.includes('Generate') || 
                                    button.textContent.includes('Create') ||
                                    button.textContent.includes('Oluştur')) {{
                                    
                                    if (button.disabled) {{
                                        return 'disabled';
                                    }}
                                    
                                    button.click();
                                    return 'clicked';
                                }}
                            }}
                            return 'not_found';
                        }})();
                    """)
                    
                    if result == 'disabled':
                        self.logger.warning("Generate button detected as disabled with JavaScript!")
                        return True
                    elif result == 'clicked':
                        self.logger.info("Generate button clicked with JavaScript (fallback)")
                        await asyncio.sleep(5)
                    else:
                        self.logger.error("Generate button not found with JavaScript")
                        return False
                        
                except Exception as fallback_error:
                    self.logger.error(f"JavaScript fallback error: {fallback_error}")
                    return False
            
            # Check for error messages
            error_selectors = [
                'div:contains("Bu isteği tamamlamak için daha fazla yapay zeka kredisi gerek")',
                'div:contains("yapay zeka kredisi")',
                'div:contains("insufficient credits")'
            ]
            
            for selector in error_selectors:
                try:
                    error_element = await self.page.find(selector)
                    if error_element:
                        self.logger.warning("Insufficient credits error detected")
                        # Close error dialog
                        close_selectors = [
                            'button:contains("Kapat")',
                            'button[aria-label*="Kapat"]'
                        ]
                        for close_selector in close_selectors:
                            try:
                                close_button = await self.page.find(close_selector)
                                if close_button:
                                    await close_button.click()
                                    self.logger.info("Error dialog closed")
                                    break
                            except:
                                continue
                        return False
                except:
                    continue
            
            self.logger.info("Video creation started")
            return True
            
        except Exception as e:
            self.logger.error(f"Video creation error: {e}")
            return False
    
    async def wait_and_download_video(self, prompt_text):
        """Wait for video creation to complete and download"""
        try:
            self.logger.info("Waiting for video creation to complete...")
            
            # Wait 30 seconds
            await asyncio.sleep(30)
            
            # Check video elements
            max_attempts = 10  # 10 attempts (total 5 minutes)
            
            for attempt in range(max_attempts):
                self.logger.info(f"Video check {attempt + 1}/{max_attempts}...")
                
                # Find all video elements
                all_videos = await self.page.find_all('video')
                self.logger.info(f"   Found video count: {len(all_videos)}")
                
                # Find video element with index=1
                video_elem = await self.page.find('div[data-index="1"] video')
                
                if video_elem:
                    self.logger.info("Index=1 video element found")
                    video_url = video_elem.get("src")
                    
                    if video_url:
                        self.logger.info(f"Video URL found: {video_url[:100]}...")
                        
                        # Download video
                        video_filename = f"video_{prompt_text[:20]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                        video_filename = "".join(c for c in video_filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                        
                        import requests
                        response = requests.get(video_url, stream=True)
                        if response.status_code == 200:
                            with open(video_filename, "wb") as f:
                                for chunk in response.iter_content(1024*1024):
                                    f.write(chunk)
                            self.logger.info(f"Video downloaded: {video_filename}")
                            return video_filename
                        else:
                            self.logger.warning(f"Video download failed, status code: {response.status_code}")
                    else:
                        self.logger.warning("Video URL not found")
                else:
                    self.logger.info("Video not ready yet, waiting...")
                
                # Wait 30 more seconds
                await asyncio.sleep(30)
            
            self.logger.warning("Video not ready - maximum wait time exceeded")
            return None
            
        except Exception as e:
            self.logger.error(f"Video download error: {e}")
            return None

def validate_request(data):
    """Validate incoming request data"""
    required_fields = ['jobId', 'prompt', 'model', 'timestamp', 'userId', 'action', 'timeout', 'callbackUrl']
    
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    return True, "Valid request"

def send_callback(callback_url, job_id, status, result_url=None, error=None):
    """Send callback to the specified URL"""
    callback_data = {
        "jobId": job_id,
        "status": status,  # "completed", "failed", "processing"
        "resultUrl": result_url,
        "error": error,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        response = requests.post(callback_url, json=callback_data, timeout=CALLBACK_TIMEOUT)
        logger.info(f"Callback sent to {callback_url} with status {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Callback failed: {e}")
        return False

def retry_on_failure(max_retries=3, delay=2):
    """Retry decorator for failed operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay * (2 ** attempt)} seconds...")
                    await asyncio.sleep(delay * (2 ** attempt))
            return None
        return wrapper
    return decorator


async def process_zendriver_job(job_data):
    """Process Zendriver job - Google Flow automation"""
    job_id = job_data['jobId']
    user_id = job_data['userId']
    prompt = job_data['prompt']
    callback_url = job_data['callbackUrl']
    
    # Send processing callback
    send_callback(callback_url, job_id, "processing")
    
    session = None
    try:
        # Create new session for each request (cookies handle login state)
        logger.info(f"Creating new session for user {user_id}")
        session = ZendriverSession(job_id, user_id)
        if not await session.create_session():
            raise Exception("Failed to create Zendriver session")
        logger.info(f"Created and stored new session for user {user_id}")
        
        # Get credentials
        credentials = session.session_manager.get_current_credentials()
        if not credentials:
            raise Exception("No credentials found")
        
        email = credentials.get('email')
        password = credentials.get('password')
        
        if not email or not password:
            raise Exception("Invalid credentials")
        
        # Smart login (will check cookies first)
        logger.info("Starting smart login process...")
        if not await session.smart_login(email, password):
            raise Exception("Login failed")
        
        # Check if user has an existing project in database
        project_id = db.get_user_project(user_id)
        if project_id:
            logger.info(f"User {user_id} has existing project from DB: {project_id}")
            
            # Check if we're already on the correct project page
            current_url = await session.page.evaluate("window.location.href")
            logger.info(f"Current browser URL: {current_url}")
            
            if project_id in current_url:
                logger.info(f"Already on project page {project_id} - skipping navigation")
            else:
                logger.info(f"Not on project page, validating access to {project_id}")
                # Validate project access
                if await session.validate_project_access(project_id):
                    logger.info(f"Project {project_id} is accessible for user {user_id}")
                else:
                    logger.warning(f"Project {project_id} is not accessible, creating new project")
                    # If project is not accessible, create new project
                    project_id = await session.create_new_project()
                    if not project_id:
                        raise Exception("Failed to create new project")
                    db.set_user_project(user_id, project_id)
                    logger.info(f"Created new project for user {user_id}: {project_id}")
        else:
            # Create new project for first time user
            logger.info(f"Creating new project for user {user_id}")
            project_id = await session.create_new_project()
            if not project_id:
                raise Exception("Failed to create new project")
            db.set_user_project(user_id, project_id)
            logger.info(f"Created new project for user {user_id}: {project_id}")
            
            # Save user credentials to database
            credentials = session.session_manager.get_current_credentials()
            if credentials and credentials.get('email'):
                db.save_user_credentials(user_id, credentials.get('email'))
        
        # Create video from text
        if not await session.create_video_from_text(prompt):
            raise Exception("Failed to create video from text")
        
        # Wait and download video
        video_filename = await session.wait_and_download_video(prompt)
        
        if video_filename:
            # Create full URL for the video file using BASE_URL
            video_url = f"{BASE_URL}/videos/{video_filename}"
            # Send success callback with video URL
            send_callback(callback_url, job_id, "completed", result_url=video_url)
            # Save successful job to database
            db.save_job_history(job_id, user_id, prompt, "completed", video_filename)
            return video_filename
        else:
            # Send success callback without video (insufficient credits)
            send_callback(callback_url, job_id, "completed", result_url="video_creation_started_but_no_credits")
            # Update user account status - credits exhausted
            db.update_account_status(user_id, "exhausted")
            # Save job without video to database
            db.save_job_history(job_id, user_id, prompt, "completed_no_credits")
            return "video_creation_started_but_no_credits"
        
    except Exception as e:
        # Send error callback
        send_callback(callback_url, job_id, "failed", error=str(e))
        # Save failed job to database
        db.save_job_history(job_id, user_id, prompt, "failed")
        raise e
    finally:
        # Close session after callback - cookies will handle login state
        if session:
            logger.info(f"Closing session for user {user_id} - cookies will handle next login")
            try:
                await session.close_session()
                logger.info(f"Session closed for user {user_id}")
            except Exception as close_error:
                logger.error(f"Error closing session for user {user_id}: {close_error}")

@app.route('/api/v1/automation/google-flow', methods=['POST'])
def google_flow_automation():
    """Google Flow automation endpoint - same as Appium pattern"""
    try:
        # Get request data
        data = request.json
        
        # Validate request
        is_valid, message = validate_request(data)
        if not is_valid:
            return jsonify({"error": message}), 400
        
        # Extract data
        job_id = data.get('jobId')
        prompt = data.get('prompt')
        model = data.get('model')
        timestamp = data.get('timestamp')
        user_id = data.get('userId')
        action = data.get('action')
        timeout = data.get('timeout')
        callback_url = data.get('callbackUrl')
        
        logger.info(f"Received Google Flow job request: {job_id} for user: {user_id}")
        logger.info(f"Action: {action}, Prompt: {prompt}")
        
        # Process job asynchronously
        import threading
        
        def run_async_job():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(process_zendriver_job(data))
            except Exception as e:
                logger.error(f"Async job error: {e}")
            # Don't close the loop to keep browser sessions alive
        
        # Start job in separate thread
        thread = threading.Thread(target=run_async_job)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "status": "accepted",
            "jobId": job_id,
            "message": "Google Flow job processing started",
            "action": action
        }), 202
        
    except Exception as e:
        logger.error(f"Error in google_flow_automation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/automation/zendriver', methods=['POST'])
def zendriver_automation():
    """Legacy Zendriver automation endpoint"""
    try:
        # Get request data
        data = request.json
        
        # Validate request
        is_valid, message = validate_request(data)
        if not is_valid:
            return jsonify({"error": message}), 400
        
        # Extract data
        job_id = data.get('jobId')
        prompt = data.get('prompt')
        model = data.get('model')
        timestamp = data.get('timestamp')
        user_id = data.get('userId')
        action = data.get('action')
        timeout = data.get('timeout')
        callback_url = data.get('callbackUrl')
        
        logger.info(f"Received job request: {job_id} for user: {user_id}")
        
        # Process job asynchronously
        import threading
        
        def run_async_job():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(process_zendriver_job(data))
            except Exception as e:
                logger.error(f"Async job error: {e}")
            # Don't close the loop to keep browser sessions alive
        
        # Start job in separate thread
        thread = threading.Thread(target=run_async_job)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "status": "accepted",
            "jobId": job_id,
            "message": "Job processing started"
        }), 202
        
    except Exception as e:
        logger.error(f"Error in zendriver_automation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "zendriver-automation",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/v1/automation/zendriver/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get job status endpoint"""
    # This would typically query a database or cache for job status
    # For now, return a placeholder response
    return jsonify({
        "jobId": job_id,
        "status": "processing",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/videos/<filename>', methods=['GET'])
def serve_video(filename):
    """Serve video files"""
    try:
        # Security check - only allow .mp4 files
        if not filename.endswith('.mp4'):
            return jsonify({"error": "Invalid file type"}), 400
        
        # Check if file exists
        if not os.path.exists(filename):
            return jsonify({"error": "Video not found"}), 404
        
        # Serve the video file
        return send_file(filename, mimetype='video/mp4')
        
    except Exception as e:
        logger.error(f"Error serving video {filename}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/v1/sessions/status', methods=['GET'])
def get_active_sessions():
    """Get status of user projects from database"""
    try:
        user_projects = db.get_all_user_projects()
        return jsonify({
            "message": "Sessions are no longer kept alive - each request creates fresh session",
            "user_projects": user_projects,
            "total_projects": len(user_projects)
        })
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/database/stats', methods=['GET'])
def get_database_stats():
    """Get database statistics"""
    try:
        user_projects = db.get_all_user_projects()
        return jsonify({
            "total_users": len(user_projects),
            "user_projects": user_projects,
            "database_path": db.db_path
        })
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/user/<user_id>/stats', methods=['GET'])
def get_user_stats(user_id):
    """Get user statistics"""
    try:
        stats = db.get_user_stats(user_id)
        project_id = db.get_user_project(user_id)
        return jsonify({
            "user_id": user_id,
            "project_id": project_id,
            "stats": stats
        })
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/database/cleanup', methods=['POST'])
def cleanup_database():
    """Clean up old database records"""
    try:
        days_old = request.json.get('days_old', 30) if request.json else 30
        deleted_count = db.cleanup_old_records(days_old)
        return jsonify({
            "message": f"Cleaned up {deleted_count} old records",
            "days_old": days_old
        })
    except Exception as e:
        logger.error(f"Error cleaning up database: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)

