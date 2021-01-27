# Twitch endpoints
TWITCH_URL = "https://www.twitch.tv"
TWITCH_API = "https://api.twitch.tv"
TWITCH_GQL = "https://gql.twitch.tv/gql"
TWITCH_WEBSOCKET = "wss://pubsub-edge.twitch.tv/v1"
TWITCH_CLIENT_ID = "kimne78kx3ncx6brgo4mv6wki5h1ko"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"

# XPath /CSS Selector and Javascript helpers
cookiePolicyCSS = 'button[data-a-target="consent-banner-accept"]'

streamCoinsMenuXP = '//div[@data-test-selector="community-points-summary"]//button'
streamCoinsMenuJS = 'document.querySelector("[data-test-selector=\'community-points-summary\']").getElementsByTagName("button")[0].click();'

streamBetTitleInBetCSS = '[data-test-selector="predictions-list-item__title"]'

streamBetCustomVoteCSS = (
    "button[data-test-selector='prediction-checkout-active-footer__input-type-toggle']"
)
streamBetCustomVoteJS = f'document.querySelector("{streamBetCustomVoteCSS}").click();'

streamBetMainDivXP = "//div[@id='channel-points-reward-center-body']//div[contains(@class,'custom-prediction-button')]"
streamBetVoteInputXP = f"({streamBetMainDivXP}//input)"
streamBetVoteButtonXP = f"({streamBetMainDivXP}//button)"

streamBetVoteInputJS = 'document.getElementById("channel-points-reward-center-body").getElementsByTagName("input")[{}].value = {};'
streamBetVoteButtonJS = 'document.getElementById("channel-points-reward-center-body").getElementsByTagName("button")[{}].click();'

streamBetTermsAcceptCSS = "button[data-test-selector='prediction-terms-step__accept-button']"
streamBetTermsAcceptJS = f'document.querySelector("{streamBetTermsAcceptCSS}").click();'

# Some Javascript code that should help the script
localStorageJS = """
window.localStorage.setItem("volume", 0);
window.localStorage.setItem("channelPointsOnboardingDismissed", true);
window.localStorage.setItem("twilight.theme", 1);
window.localStorage.setItem("mature", true);
window.localStorage.setItem("rebrand-notice-dismissed", true);
window.localStorage.setItem("emoteAnimationsEnabled", false);
window.localStorage.setItem("chatPauseSetting", "ALTKEY");
"""
clearStyleChatJS = """
var item = document.querySelector('[data-test-selector="chat-scrollable-area__message-container"]');
if (item) {
    var parent = item.closest("div.simplebar-scroll-content");
    if(parent) parent.hidden = true;
}
var header = document.querySelector('[data-test-selector="channel-leaderboard-container"]');
if(header) header.hidden = true;
"""
maximizeBetWindowJS = """
var absolute = document.querySelector('[aria-describedby="channel-points-reward-center-body"]').closest("div.tw-absolute")
if(absolute) absolute.classList.remove("tw-absolute")

document.getElementsByClassName("reward-center__content")[0].style.width = "44rem";
document.getElementsByClassName("reward-center__content")[0].style.height = "55rem";

document.querySelector('[aria-describedby="channel-points-reward-center-body"]').style["max-height"] = "55rem";

document.getElementsByClassName("reward-center-body")[0].style["max-width"] = "44rem";
// document.getElementsByClassName("reward-center-body")[0].style["min-height"] = "55rem";
"""
scrollDownBetWindowJS = """
var scrollable = document.getElementById("channel-points-reward-center-body").closest("div.simplebar-scroll-content");
scrollable.scrollTop = scrollable.scrollHeight;
"""
