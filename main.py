import logging
import sys
import traceback
import time
import os

from DrissionPage import ChromiumPage, ChromiumOptions
from src.utils import CONFIG, sendNotification, getProjectRoot
from src.CloudflareBypasser import CloudflareBypasser

def setupLogging():
    _format = CONFIG['logging']['format']
    _level = CONFIG['logging']['level']
    terminalHandler = logging.StreamHandler(sys.stdout)
    terminalHandler.setFormatter(logging.Formatter(_format))

    logs_directory = getProjectRoot() / "logs"
    logs_directory.mkdir(parents=True, exist_ok=True)

    fileHandler = logging.FileHandler(logs_directory / "activity.log", encoding="utf-8")
    fileHandler.setFormatter(logging.Formatter(_format))
    fileHandler.setLevel(logging.getLevelName(_level.upper()))

    logging.basicConfig(
        level=logging.getLevelName(_level.upper()),
        format=_format,
        handlers=[
            terminalHandler,
            fileHandler,
        ],
    )

def get_chromium_options(browser_path: str, arguments: list) -> ChromiumOptions:
    options = ChromiumOptions().auto_port()
    options.set_paths(browser_path=browser_path)
    for argument in arguments:
        options.set_argument(argument)
    return options

def bypass_cloudflare(driver):
    logging.info('Starting Cloudflare bypass.')
    cf_bypasser = CloudflareBypasser(driver)
    cf_bypasser.bypass()
    logging.info("Cloudflare bypass completed.")

def open_url_in_chrome(driver, url, duration):
    logging.info('Opening the URL in Chrome...')
    driver.get(url)
    # Keep the browser open for the specified duration
    logging.info(f'Keeping the browser open for {duration} seconds.')
    time.sleep(duration * 60)  # Convert minutes to seconds
    # You can add more interactions here if needed

def main():
    setupLogging()

    url = CONFIG['url']
    duration = CONFIG['duration']

    try:
        browser_path = os.getenv('CHROME_PATH', "/usr/bin/google-chrome")
        arguments = [
            "-no-first-run",
            "-force-color-profile=srgb",
            "-metrics-recording-only",
            "-password-store=basic",
            "-use-mock-keychain",
            "-export-tagged-pdf",
            "-no-default-browser-check",
            "-disable-background-mode",
            "-enable-features=NetworkService,NetworkServiceInProcess,LoadCryptoTokenExtension,PermuteTLSExtensions",
            "-disable-features=FlashDeprecationWarning,EnablePasswordsAccountStorage",
            "-deny-permission-prompts",
            "-disable-gpu",
            "-accept-lang=en-US",
        ]
        options = get_chromium_options(browser_path, arguments)

        # Initialize the browser and bypass Cloudflare
        driver = ChromiumPage(addr_or_opts=options)
        logging.info("Bypassing Cloudflare for the URL...")
        driver.get(url)
        bypass_cloudflare(driver)
        
        # Continue using the same browser instance to open the URL
        logging.info("Cloudflare bypass successful. Opening the URL in Chrome...")
        open_url_in_chrome(driver, url, duration)
        
    except Exception as e:
        logging.exception("")
        sendNotification("⚠️ Error occurred, please check the log", traceback.format_exc(), e)
    finally:
        logging.info('Closing the browser.')
        driver.quit()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception("")
        sendNotification("⚠️ Error occurred, please check the log", traceback.format_exc(), e)
        exit(1)
