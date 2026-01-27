from typing import Any, Dict
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlowResult,
    OptionsFlowWithConfigEntry
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import (
    DOMAIN,
    CONF_JSESSIONID,
    CONF_UPDATE_INTERVAL,
    CONF_UPDATE_INTERVAL_DEFAULT,
    CONF_ACTIVE_MODE_SMARTTAGS,
    CONF_ACTIVE_MODE_SMARTTAGS_DEFAULT,
    CONF_ACTIVE_MODE_OTHERS,
    CONF_ACTIVE_MODE_OTHERS_DEFAULT,
    VERSION,
    BUILD_INFO
)
from .utils import gen_qr_code_base64
from .auth import (
    get_entry_point,
    create_signin_url,
    decrypt_response,
    get_user_auth_token,
    get_api_token,
    generate_code_challenge,
    generate_state
)
import asyncio
import logging
from urllib.parse import parse_qs


_LOGGER = logging.getLogger(__name__)

# Log version information on import
_LOGGER.info(f"SmartThings Find Integration {BUILD_INFO}")

class SmartThingsFindConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SmartThings Find."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    reauth_entry: ConfigEntry | None = None

    task_stage_one: asyncio.Task | None = None
    task_stage_two: asyncio.Task | None = None

    qr_url = None
    session = None
    jsessionid = None
    
    # New auth flow variables
    code_verifier = None
    auth_state = None
    chk_do_num = None
    auth_code = None
    auth_server_url = None
    api_token = None
    
    error = None

    async def do_stage_one(self):
        """Initialize OAuth2 authentication flow."""
        _LOGGER.debug("Starting OAuth2 authentication flow")
        try:
            self.session = async_get_clientsession(self.hass)
            
            # Generate PKCE parameters
            code_challenge, self.code_verifier = generate_code_challenge()
            self.auth_state = generate_state()
            
            # Get entry point
            entry_point = await get_entry_point(self.session)
            
            # Create sign-in URL
            signin_url, state, chk_do_num = create_signin_url(
                entry_point, code_challenge, self.auth_state
            )
            self.chk_do_num = chk_do_num
            
            # Generate QR code
            self.qr_url = signin_url
            _LOGGER.info(f"Generated QR URL for authentication")
            
        except Exception as e:
            self.error = "Authentication initialization failed. Check logs for details."
            _LOGGER.error(f"Exception in auth stage 1: {e}", exc_info=True)

    async def do_stage_two(self):
        """Complete OAuth2 authentication flow."""
        _LOGGER.debug("Completing OAuth2 authentication flow")
        try:
            # For now, we'll need to simulate the callback from the redirect
            # In a real implementation, this would handle the redirect callback
            # For Home Assistant, we need to poll or use a different mechanism
            
            # This is a simplified version - in reality, we'd need to handle
            # the OAuth2 callback properly within Home Assistant's constraints
            
            # For now, let's create a fallback to manual JSESSIONID entry
            # until we can implement the full OAuth2 flow
            self.error = "OAuth2 flow not fully implemented yet. Please use manual JSESSIONID entry."
            _LOGGER.warning("OAuth2 flow not fully implemented")
            
        except Exception as e:
            self.error = "Authentication completion failed. Check logs for details."
            _LOGGER.error(f"Exception in auth stage 2: {e}", exc_info=True)


    
    # Second step: Show QR code and wait for user to scan
    async def async_step_auth_stage_two(self, user_input=None):
        """Show QR code for authentication."""
        _LOGGER.debug(f"async_step_auth_stage_two called with user_input: {user_input}")
        
        if user_input is not None:
            # User clicked continue - for now, fall back to manual entry
            # In the future, we could poll for completion here
            return await self.async_step_finish()
        
        # Show form with QR code info
        _LOGGER.debug(f"Showing QR code form, URL: {self.qr_url[:50] if self.qr_url else 'None'}...")
        
        return self.async_show_form(
            step_id="auth_stage_two",
            data_schema=vol.Schema({}),
            description_placeholders={
                "qr_url": self.qr_url or "Error generating QR URL",
                "message": "Scan the QR code with your Samsung device, or copy the URL. After authenticating, click Submit to continue with manual JSESSIONID entry."
            }
        )

    async def async_step_user(self, user_input=None):
        """Start the authentication flow."""
        return await self.async_step_auth_choice(user_input)
    
    async def async_step_auth_choice(self, user_input=None):
        """Let user choose authentication method."""
        _LOGGER.debug(f"async_step_auth_choice called with user_input: {user_input}")
        
        if user_input is not None:
            auth_method = user_input.get("auth_method")
            _LOGGER.debug(f"Selected auth method: {auth_method}")
            
            if auth_method == "oauth2":
                # Start OAuth2 flow - do initialization directly
                _LOGGER.debug("Starting OAuth2 flow")
                await self.do_stage_one()
                
                if self.error:
                    _LOGGER.error(f"OAuth2 init failed: {self.error}")
                    return self.async_show_form(
                        step_id="auth_choice",
                        data_schema=vol.Schema({
                            vol.Required("auth_method", default="manual"): vol.In({
                                "oauth2": "QR Code Authentication (Recommended)",
                                "manual": "Manual JSESSIONID Entry"
                            })
                        }),
                        errors={"base": "auth_failed"}
                    )
                
                # Move to stage two (show QR code)
                return await self.async_step_auth_stage_two()
            else:
                # Use manual JSESSIONID entry
                _LOGGER.debug("Using manual JSESSIONID entry - moving to finish")
                return await self.async_step_finish()
        
        data_schema = vol.Schema({
            vol.Required("auth_method", default="manual"): vol.In({
                "oauth2": "QR Code Authentication (Recommended)",
                "manual": "Manual JSESSIONID Entry"
            })
        })
        _LOGGER.debug("Showing auth choice form")
        return self.async_show_form(
            step_id="auth_choice",
            data_schema=data_schema,
            description_placeholders={
                "message": "Choose your preferred authentication method. QR code authentication is more secure and easier to use."
            }
        )

    async def async_step_finish(self, user_input=None):
        """Prompt for JSESSIONID and create entry."""
        errors = {}
        if user_input is not None:
            jsessionid = user_input.get(CONF_JSESSIONID)
            if not jsessionid:
                errors["base"] = "missing_jsessionid"
            else:
                data = {CONF_JSESSIONID: jsessionid}
                return self.async_create_entry(title="SmartThings Find", data=data)

        data_schema = vol.Schema({
            vol.Required(CONF_JSESSIONID): str
        })
        return self.async_show_form(
            step_id="finish",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "message": "Enter your JSESSIONID from the SmartThings Find website. See the README for instructions on how to obtain this."
            }
        )

    
    async def async_step_reauth(self, user_input=None):
        self.reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        if user_input is None:
            return self.async_show_form(
                step_id="auth_choice",
                data_schema=vol.Schema({}),
                description_placeholders={
                    "message": "Re-authentication required. Please choose your authentication method."
                }
            )
        return await self.async_step_user()
    
    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        return await self.async_step_reauth_confirm(self)
    
    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return SmartThingsFindOptionsFlowHandler(config_entry)
    
    
class SmartThingsFindOptionsFlowHandler(OptionsFlowWithConfigEntry):
    """Handle an options flow."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle options flow."""

        if user_input is not None:

            res = self.async_create_entry(title="", data=user_input)

            # Reload the integration entry to make sure the newly set options take effect
            self.hass.config_entries.async_schedule_reload(self.config_entry.entry_id)
            return res

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_UPDATE_INTERVAL,
                    default=self.options.get(
                        CONF_UPDATE_INTERVAL, CONF_UPDATE_INTERVAL_DEFAULT
                    ),
                ): vol.All(vol.Coerce(int), vol.Clamp(min=30)),
                vol.Optional(
                    CONF_ACTIVE_MODE_SMARTTAGS,
                    default=self.options.get(
                        CONF_ACTIVE_MODE_SMARTTAGS, CONF_ACTIVE_MODE_SMARTTAGS_DEFAULT
                    ),
                ): bool,
                vol.Optional(
                    CONF_ACTIVE_MODE_OTHERS,
                    default=self.options.get(
                        CONF_ACTIVE_MODE_OTHERS, CONF_ACTIVE_MODE_OTHERS_DEFAULT
                    ),
                ): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=data_schema)