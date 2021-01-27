import time
import logging
import random
import os
import platform

from millify import prettify
from pathlib import Path
from datetime import datetime
from enum import Enum, auto
from PIL import Image, ImageDraw, ImageFont

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, JavascriptException

from TwitchChannelPointsMiner.classes.EventPrediction import EventPrediction
from TwitchChannelPointsMiner.utils import bet_condition
from TwitchChannelPointsMiner.constants import (
    TWITCH_URL,
    cookiePolicyCSS,
    streamCoinsMenuXP,
    streamCoinsMenuJS,
    streamBetTitleInBetCSS,
    streamBetCustomVoteCSS,
    streamBetCustomVoteJS,
    streamBetMainDivXP,
    streamBetVoteInputXP,
    streamBetVoteButtonXP,
    streamBetVoteInputJS,
    streamBetVoteButtonJS,
    streamBetTermsAcceptCSS,
    streamBetTermsAcceptJS,
    localStorageJS,
    clearStyleChatJS,
    maximizeBetWindowJS,
    scrollDownBetWindowJS,
)

logger = logging.getLogger(__name__)


class Browser(Enum):
    CHROME = auto()
    FIREFOX = auto()


class BrowserSettings:
    def __init__(
        self,
        timeout: float = 10.0,
        implicitly_wait: int = 5,
        max_attempts: int = 3,
        do_screenshot: bool = False,  # Options for debug
        save_html: bool = False,  # Options for debug
        show: bool = True,
        browser: Browser = Browser.FIREFOX,
        driver_path: str = None,
    ):
        self.timeout = timeout
        self.implicitly_wait = implicitly_wait
        self.max_attempts = max_attempts
        self.do_screenshot = do_screenshot
        self.save_html = save_html
        self.show = show
        self.browser = browser
        self.driver_path = (
            driver_path
            if driver_path is not None
            else os.path.join(
                Path().absolute(),
                (
                    ("chromedriver" if browser == Browser.CHROME else "geckodriver")
                    + (".exe" if platform.system() == "Windows" else "")
                ),
            )
        )


class TwitchBrowser:
    def __init__(
        self,
        auth_token: str,
        session_id: str,
        settings: BrowserSettings,
    ):
        self.auth_token = auth_token
        self.session_id = session_id
        self.settings = settings

        self.currently_is_betting = False
        self.browser = None

    def init(self):
        if self.settings.browser == Browser.FIREFOX:
            self.__init_firefox()
        elif self.settings.browser == Browser.CHROME:
            self.__init_chrome()
        else:
            logger.critical(f"{self.settings.browser} not supported! Close the script")
            exit(1)

        if self.browser is not None:
            self.browser.set_window_size(450, 800)
            self.browser.implicitly_wait(self.settings.implicitly_wait)
            self.__init_twitch()
        else:
            logger.critical("Something went wrong! Unable to start the browser. Close the script")
            exit(1)

    def __init_twitch(self):
        logger.debug(
            "Init Twitch page - Cookies - LocalStorage items",
            extra={"emoji": ":wrench:"},
        )
        cookie = {
            "domain": ".twitch.tv",
            "hostOnly": False,
            "httpOnly": False,
            "name": "auth-token",
            "path": "/",
            "SameSite": "no_restriction",
            "secure": True,
            "session": False,
            "storeId": "0",
            "id": 1,
            "value": self.auth_token,
        }
        self.browser.get(TWITCH_URL)
        self.browser.add_cookie(cookie)
        time.sleep(random.uniform(2.5, 3.5))

        self.__click_when_exist(cookiePolicyCSS, By.CSS_SELECTOR, suppress_error=True)
        time.sleep(random.uniform(0.5, 1.5))

        # Edit value in localStorage for dark theme, point consent etc.
        self.__execute_script(localStorageJS)
        time.sleep(random.uniform(0.5, 1.5))
        self.__blank()

    def __blank(self):
        self.browser.get("about:blank")

    def __execute_script(self, javascript_code, suppress_error=False):
        try:
            self.browser.execute_script(javascript_code)
            return True
        except JavascriptException:
            if suppress_error is False:
                logger.warning(f"Failed to execute: {javascript_code}")
        return False

    # Private method __ - We can instantiate webdriver only with init_browser
    def __init_chrome(self):
        logger.debug("Init Chrome browser", extra={"emoji": ":wrench:"})
        options = webdriver.ChromeOptions()
        if not self.settings.show:
            options.add_argument("headless")

        options.add_argument("mute-audio")
        options.add_argument("disable-dev-shm-usage")
        options.add_argument("disable-accelerated-2d-canvas")
        options.add_argument("no-first-run")
        options.add_argument("no-zygote")
        options.add_argument("disable-gpu")
        options.add_argument("no-sandbox")
        options.add_argument("disable-setuid-sandbox")
        options.add_argument("disable-infobars")
        options.add_argument(
            "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
        )

        options.add_experimental_option(
            "prefs", {"profile.managed_default_content_settings.images": 2}
        )
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option(
            "excludeSwitches", ["enable-automation", "enable-logging"]
        )

        if os.path.isfile(self.settings.driver_path) is True:
            self.browser = webdriver.Chrome(self.settings.driver_path, options=options)
        else:
            logger.warning(
                f"The path {self.settings.driver_path} is not valid. Use default path",
                extra={"emoji": ":wrench:"},
            )
            self.browser = webdriver.Chrome(options=options)

    # Private method __ - We can instantiate webdriver only with init_browser
    def __init_firefox(self):
        logger.debug("Init Firefox browser", extra={"emoji": ":wrench:"})
        options = webdriver.FirefoxOptions()
        if not self.settings.show:
            options.headless = True

        fp = webdriver.FirefoxProfile()
        fp.set_preference("permissions.default.image", 2)
        fp.set_preference("permissions.default.stylesheet", 2)
        fp.set_preference("dom.ipc.plugins.enabled.libflashplayer.so", "false")
        fp.set_preference("media.volume_scale", "0.0")
        fp.set_preference("browser.startup.homepage", "about:blank")
        fp.set_preference("startup.homepage_welcome_url", "about:blank")
        fp.set_preference("startup.homepage_welcome_url.additional", "about:blank")
        fp.set_preference(
            "general.useragent.override",
            "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:56.0) Gecko/20100101 Firefox/56.0",
        )

        if os.path.isfile(self.settings.driver_path) is True:
            self.browser = webdriver.Firefox(
                executable_path=self.settings.driver_path,
                options=options,
                firefox_profile=fp,
            )
        else:
            logger.warning(
                f"The path {self.settings.driver_path} is not valid. Use default path",
                extra={"emoji": ":wrench:"},
            )
            self.browser = webdriver.Firefox(options=options, firefox_profile=fp)

    def __debug(self, event, method):
        if self.settings.do_screenshot:
            self.screenshot(f"{event.event_id}___{method}")
        if self.settings.save_html:
            self.save_html(f"{event.event_id}___{method}")

    def save_html(self, fname):
        htmls_path = os.path.join(Path().absolute(), "htmls")
        Path(htmls_path).mkdir(parents=True, exist_ok=True)
        Path(os.path.join(htmls_path, self.session_id)).mkdir(
            parents=True, exist_ok=True
        )

        fname = f"{fname}.html" if fname.endswith(".html") is False else fname
        fname = fname.replace(".html", f".{time.time()}.html")
        fname = os.path.join(htmls_path, self.session_id, fname)

        # Little delay ...
        time.sleep(0.2)
        with open(fname, "w", encoding="utf-8") as writer:
            writer.write(self.browser.page_source)

    def screenshot(self, fname, write_timestamp=False):
        screenshots_path = os.path.join(Path().absolute(), "screenshots")
        Path(screenshots_path).mkdir(parents=True, exist_ok=True)
        Path(os.path.join(screenshots_path, self.session_id)).mkdir(
            parents=True, exist_ok=True
        )

        fname = f"{fname}.png" if fname.endswith(".png") is False else fname
        fname = fname.replace(".png", f".{time.time()}.png")
        fname = os.path.join(screenshots_path, self.session_id, fname)
        # Little pause prevent effect/css animations in browser delayed
        time.sleep(0.1)
        self.browser.save_screenshot(fname)

        try:
            if write_timestamp is True:
                time.sleep(0.5)
                image = Image.open(fname)
                draw = ImageDraw.Draw(image)

                font = ImageFont.truetype(
                    os.path.join(Path().absolute(), "assets", "Roboto-Bold.ttf"),
                    size=35,
                )
                (x, y) = (15, image.height // 3)
                datetime_text = datetime.now().strftime("%d/%m %H:%M:%S.%f")

                shadowcolor = "rgb(0, 0, 0)"  # black color
                # Thin border
                draw.text((x - 1, y), datetime_text, font=font, fill=shadowcolor)
                draw.text((x + 1, y), datetime_text, font=font, fill=shadowcolor)
                draw.text((x, y - 1), datetime_text, font=font, fill=shadowcolor)
                draw.text((x, y + 1), datetime_text, font=font, fill=shadowcolor)

                # Thicker border
                draw.text((x - 1, y - 1), datetime_text, font=font, fill=shadowcolor)
                draw.text((x + 1, y - 1), datetime_text, font=font, fill=shadowcolor)
                draw.text((x - 1, y + 1), datetime_text, font=font, fill=shadowcolor)
                draw.text((x + 1, y + 1), datetime_text, font=font, fill=shadowcolor)

                color = "rgb(255, 255, 255)"  # white color
                draw.text((x, y), datetime_text, font=font, fill=color)
                image.save(fname, optimize=True, quality=20)
        except Exception:
            logger.error(
                f"Exception raised during screenshot file {fname}", exc_info=True
            )

    def __click_when_exist(
        self,
        selector,
        by: By = By.CSS_SELECTOR,
        suppress_error=False,
        timeout=None,
        javascript=None,
    ):
        timeout = self.settings.timeout if timeout is None else timeout
        try:
            element = WebDriverWait(self.browser, timeout).until(
                expected_conditions.element_to_be_clickable((by, selector))
            )
            ActionChains(self.browser).move_to_element(element).click().perform()
            return True
        except Exception:
            if suppress_error is False:
                logger.error(f"Exception raised with: {selector}", exc_info=True)

            if javascript is not None:
                return self.__execute_script(javascript, suppress_error=suppress_error)

        return False

    def __send_text(
        self,
        selector,
        text,
        by: By = By.CSS_SELECTOR,
        suppress_error=False,
        javascript=None,
    ):
        try:
            element = WebDriverWait(self.browser, self.settings.timeout).until(
                expected_conditions.element_to_be_clickable((by, selector))
            )
            ActionChains(self.browser).move_to_element(element).click().send_keys(
                text
            ).perform()
            return True
        except Exception:
            if suppress_error is False:
                logger.error(f"Exception raised with: {selector}", exc_info=True)

            if javascript is not None:
                return self.__execute_script(javascript)

        return False

    def start_bet(self, event: EventPrediction):
        start_time = time.time()
        if bet_condition(self, event, logger) is True:
            for attempt in range(0, self.settings.max_attempts):
                logger.info(
                    f"Start betting for {event} owned by {event.streamer}",
                    extra={"emoji": ":wrench:"},
                )
                self.browser.get(event.streamer.chat_url)
                time.sleep(random.uniform(3, 5))
                self.__click_when_exist(
                    cookiePolicyCSS, By.CSS_SELECTOR, suppress_error=True, timeout=1.5
                )

                # Hide the chat ... Don't ask me why
                self.__execute_script(clearStyleChatJS, suppress_error=True)

                if self.__bet_chains_methods(event) is True:
                    return self.currently_is_betting, time.time() - start_time
                logger.error(
                    f"Attempt {attempt+1} failed!", extra={"emoji": ":wrench:"}
                )
            self.__blank()  # If we fail return to blank page
        return False, time.time() - start_time

    def __bet_chains_methods(self, event):
        if self.__open_coins_menu(event) is True:
            if self.__click_on_bet(event) is True:
                if self.__enable_custom_bet_value(event) is True:
                    return True
        return False

    def place_bet(self, event: EventPrediction):
        logger.info(
            f"Going to complete bet for {event} owned by {event.streamer}",
            extra={"emoji": ":wrench:"},
        )
        if event.status == "ACTIVE":
            if event.box_fillable and self.currently_is_betting:

                div_bet_is_open = False
                self.__debug(event, "place_bet")
                try:
                    WebDriverWait(self.browser, 1).until(
                        expected_conditions.visibility_of_element_located(
                            (By.XPATH, streamBetMainDivXP)
                        )
                    )
                    div_bet_is_open = True
                except TimeoutException:
                    logger.info(
                        "The bet div was not found, maybe It was closed. Attempt to open again, hope to be in time",
                        extra={"emoji": ":wrench:"},
                    )
                    div_bet_is_open = self.__bet_chains_methods(event)
                    if div_bet_is_open is True:
                        logger.info(
                            "Success! Bet div is now open, we can complete the bet",
                            extra={"emoji": ":wrench:"},
                        )

                if div_bet_is_open is True:
                    decision = event.bet.calculate(event.streamer.channel_points)
                    if decision["choice"]:
                        selector_index = 1 if decision["choice"] == "A" else 2
                        logger.info(
                            f"Decision: {event.bet.get_outcome(selector_index - 1)}",
                            extra={"emoji": ":wrench:"},
                        )

                        try:
                            logger.info(
                                f"Going to write: {prettify(decision['amount'], '.')} channel points on input {decision['choice']}",
                                extra={"emoji": ":wrench:"},
                            )
                            if (
                                self.__send_text_on_bet(
                                    event, selector_index, decision["amount"]
                                )
                                is True
                            ):
                                logger.info(
                                    f"Going to place the bet for {event}",
                                    extra={"emoji": ":wrench:"},
                                )
                                if self.__click_on_vote(event, selector_index) is True:

                                    if self.__accept_bet_terms(event, timeout=1.5):
                                        logger.info(
                                            "Agree to Predictions Terms & Conditions",
                                            extra={"emoji": ":wrench:"},
                                        )

                                    event.bet_placed = True
                                    time.sleep(random.uniform(5, 10))
                        except Exception:
                            logger.error("Exception raised", exc_info=True)
                else:
                    logger.info(
                        "Sorry, unable to complete the bet. The bet div still closed"
                    )
            else:
                logger.info(
                    f"Sorry, unable to complete the bet. Event box fillable: {event.box_fillable}, the browser is betting: {self.currently_is_betting}"
                )
        else:
            logger.info(
                f"Oh no! The event It's not more ACTIVE, current status: {event.status}",
                extra={"emoji": ":disappointed_relieved:"},
            )

        self.browser.get("about:blank")
        self.currently_is_betting = False

    def __open_coins_menu(self, event: EventPrediction):
        logger.info(f"Open coins menu for {event}", extra={"emoji": ":wrench:"})
        if (
            self.__click_when_exist(
                streamCoinsMenuXP, By.XPATH, javascript=streamCoinsMenuJS
            )
            is True
        ):
            time.sleep(random.uniform(0.01, 0.1))
            self.__debug(event, "open_coins_menu")
            return True
        return False

    def __click_on_bet(self, event, maximize_div=True):
        logger.info(f"Click on the bet for {event}", extra={"emoji": ":wrench:"})
        if self.__click_when_exist(streamBetTitleInBetCSS, By.CSS_SELECTOR) is True:
            time.sleep(random.uniform(0.01, 0.1))
            if maximize_div is True:
                # Edit the css for make the window full-screen in browser. Another useless change
                self.__execute_script(maximizeBetWindowJS, suppress_error=True)
            self.__debug(event, "click_on_bet")
            return True
        return False

    def __enable_custom_bet_value(self, event, scroll_down=True):
        logger.info(
            f"Enable input of custom value for {event}",
            extra={"emoji": ":wrench:"},
        )

        if scroll_down is True:
            time.sleep(random.uniform(0.01, 0.1))
            if self.__execute_script(scrollDownBetWindowJS) is False:
                logger.error("Unable to scroll down in the bet window")

        if (
            self.__click_when_exist(
                streamBetCustomVoteCSS,
                By.CSS_SELECTOR,
                javascript=streamBetCustomVoteJS,
            )
            is True
        ):
            time.sleep(random.uniform(0.01, 0.1))
            self.__debug(event, "enable_custom_bet_value")
            event.box_fillable = True
            self.currently_is_betting = True
            return True
        else:
            logger.info(
                "Something went wrong unable to continue with betting - Fillable box not avaible"
            )
        return False

    def __send_text_on_bet(self, event, selector_index, text):
        self.__debug(event, "before__send_text")
        if (
            self.__send_text(
                f"{streamBetVoteInputXP}[{selector_index}]",
                text,
                By.XPATH,
                javascript=streamBetVoteInputJS.format(
                    int(selector_index) - 1, int(text)
                ),
            )
            is True
        ):
            self.__debug(event, "send_text")
            return True
        return False

    def __click_on_vote(self, event, selector_index):
        if (
            self.__click_when_exist(
                f"{streamBetVoteButtonXP}[{selector_index}]",
                By.XPATH,
                javascript=streamBetVoteButtonJS.format(int(selector_index) - 1),
            )
            is True
        ):
            self.__debug(event, "click_on_vote")
            return True
        return False

    def __accept_bet_terms(self, event, timeout=1.5):
        if (
            self.__click_when_exist(
                streamBetTermsAcceptCSS,
                By.CSS_SELECTOR,
                suppress_error=True,
                timeout=timeout,
                javascript=streamBetTermsAcceptJS,
            )
            is True
        ):
            self.__debug(event, "accept_bet_term")
            return True
        return False
