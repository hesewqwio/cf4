import logging
import sys
import traceback
import time
import os

from DrissionPage import ChromiumPage, ChromiumOptions
from src import Browser, Searches
from src.utils import CONFIG, sendNotification, getProjectRoot
from src.CloudflareBypasser import CloudflareBypasser

def setupLogging():
    _format = CONFIG['logging']['format']
    _level = CONFIG['logging']['level']
    terminalHandler = logging.StreamHandler(sys.stdout)
    terminalHandler.setFormatter(logging.Formatter(_format))

    logs_directory = getProjectRoot() / "logs"
    logs_directory.mkdir(parents=True, exist_ok=True)

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": True,
        }
    )
    logging.basicConfig(
        level=logging.getLevelName(_level.upper()),
        format=_format,
        handlers=[
            handlers.TimedRotatingFileHandler(
                logs_directory / "activity.log",
                when="midnight",
                interval=1,
                backupCount=2,
                encoding="utf-8",
            ),
            terminalHandler,
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

def perform_searches(mobile):
    with Browser(mobile=mobile) as browser:
        searches = Searches(browser=browser)
        searches.performSearch(CONFIG['url'], CONFIG['duration'])
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
        driver = ChromiumPage(addr_or_opts=options)
        driver.get(CONFIG['url'])
        bypass_cloudflare(driver)
        driver.quit()

def main():
    setupLogging()

    search_type = CONFIG['search']['type']

    try:
        if search_type in ("desktop", "both"):
            logging.info("Performing desktop searches...")
            perform_searches(mobile=False)

        if search_type in ("mobile", "both"):
            logging.info("Performing mobile searches...")
            perform_searches(mobile=True)

    except Exception as e:
        logging.exception("")
        sendNotification("⚠️ Error occurred, please check the log", traceback.format_exc(), e)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception("")
        sendNotification("⚠️ Error occurred, please check the log", traceback.format_exc(), e)
        exit(1)
