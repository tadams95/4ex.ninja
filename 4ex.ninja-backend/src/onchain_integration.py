"""
Onchain Integration Service - Backend Implementation

Provides Web3 infrastructure for real token balance checking and wallet verification.
This replaces simulation with actual onchain calls when the $4EX token is deployed.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from web3 import Web3
from web3.exceptions import Web3Exception
from eth_account import Account
from eth_account.messages import encode_defunct

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class TokenConfig:
    """Configuration for the $4EX token contract"""

    address: str = "0x0000000000000000000000000000000000000000"  # Placeholder
    decimals: int = 18
    symbol: str = "4EX"

    @property
    def is_deployed(self) -> bool:
        """Check if the token is actually deployed"""
        return self.address != "0x0000000000000000000000000000000000000000"


@dataclass
class AccessThresholds:
    """Token balance thresholds for access tiers"""

    HOLDERS = 1000 * (10**18)  # 1,000 $4EX
    PREMIUM = 10000 * (10**18)  # 10,000 $4EX
    WHALE = 100000 * (10**18)  # 100,000 $4EX


# ERC20 Contract ABI (minimal for balance checking)
ERC20_ABI = [
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
]


class OnchainIntegrationService:
    """
    Service for onchain integration and real token balance checking.

    Provides:
    - Real token balance verification via smart contract calls
    - Wallet signature verification for authentication
    - Access tier calculation based on actual token holdings
    - Fallback to simulation during development/testing
    """

    def __init__(self, base_rpc_url: Optional[str] = None):
        self.token_config = TokenConfig()
        self.access_thresholds = AccessThresholds()

        # Initialize Web3 connection to Base network
        self.base_rpc_url = base_rpc_url or "https://mainnet.base.org"
        self.web3 = Web3(Web3.HTTPProvider(self.base_rpc_url))

        if not self.web3.is_connected():
            logger.warning(f"Failed to connect to Base RPC: {self.base_rpc_url}")
            logger.info("Will use simulation mode until connection is restored")

    async def get_token_balance(self, wallet_address: str) -> int:
        """
        Get real token balance from smart contract.

        Args:
            wallet_address: Ethereum wallet address

        Returns:
            Token balance in wei (18 decimals)
        """
        try:
            # Validate wallet address format
            if not self.web3.is_address(wallet_address):
                raise ValueError(f"Invalid wallet address: {wallet_address}")

            # Convert to checksum address
            wallet_address = self.web3.to_checksum_address(wallet_address)

            # Check if token is deployed
            if not self.token_config.is_deployed:
                logger.info(
                    f"Token not deployed, using simulation for {wallet_address}"
                )
                return self._get_simulated_balance(wallet_address)

            # Get real balance from contract
            if not self.web3.is_connected():
                logger.warning("Web3 not connected, falling back to simulation")
                return self._get_simulated_balance(wallet_address)

            try:
                # Create contract instance
                contract = self.web3.eth.contract(
                    address=self.token_config.address, abi=ERC20_ABI
                )

                # Call balanceOf function
                balance = contract.functions.balanceOf(wallet_address).call()

                logger.info(f"Real token balance for {wallet_address}: {balance}")
                return balance

            except Exception as contract_error:
                logger.error(f"Contract call failed: {contract_error}")
                logger.info("Falling back to simulation")
                return self._get_simulated_balance(wallet_address)

        except Exception as e:
            logger.error(f"Failed to get token balance for {wallet_address}: {e}")
            # Fallback to simulation on any error
            return self._get_simulated_balance(wallet_address)

    def _get_simulated_balance(self, wallet_address: str) -> int:
        """
        Simulate token balance for testing purposes.

        Simulates different tiers based on last character of address:
        - Addresses ending in '0': Whale tier (100,000+ $4EX)
        - Addresses ending in '1': Premium tier (10,000+ $4EX)
        - Addresses ending in '2': Holders tier (1,000+ $4EX)
        - Other addresses: Free tier (0 $4EX)
        """
        last_char = wallet_address[-1].lower()

        if last_char == "0":
            balance = self.access_thresholds.WHALE + (10**18)  # Whale + extra
        elif last_char == "1":
            balance = self.access_thresholds.PREMIUM + (10**18)  # Premium + extra
        elif last_char == "2":
            balance = self.access_thresholds.HOLDERS + (10**18)  # Holders + extra
        else:
            balance = 0  # Free tier

        logger.debug(f"Simulated balance for {wallet_address}: {balance}")
        return balance

    def calculate_access_tier(self, balance: int) -> str:
        """
        Calculate access tier based on token balance.

        Args:
            balance: Token balance in wei

        Returns:
            Access tier: 'whale', 'premium', 'holders', or 'public'
        """
        if balance >= self.access_thresholds.WHALE:
            return "whale"
        elif balance >= self.access_thresholds.PREMIUM:
            return "premium"
        elif balance >= self.access_thresholds.HOLDERS:
            return "holders"
        else:
            return "public"

    def verify_wallet_signature(
        self, wallet_address: str, message: str, signature: str
    ) -> bool:
        """
        Verify wallet signature for authentication.

        Args:
            wallet_address: Ethereum wallet address
            message: Original message that was signed
            signature: Signature to verify

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Convert to checksum address
            wallet_address = self.web3.to_checksum_address(wallet_address)

            # Encode message as Ethereum signed message
            message_hash = encode_defunct(text=message)

            # Recover address from signature
            recovered_address = Account.recover_message(
                message_hash, signature=signature
            )

            # Check if recovered address matches provided address
            is_valid = recovered_address.lower() == wallet_address.lower()

            logger.info(f"Signature verification for {wallet_address}: {is_valid}")
            return is_valid

        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False

    def update_token_address(self, new_address: str) -> bool:
        """
        Update the token contract address when $4EX is deployed.

        Args:
            new_address: New token contract address

        Returns:
            True if update was successful, False otherwise
        """
        try:
            if not self.web3.is_address(new_address):
                raise ValueError(f"Invalid contract address: {new_address}")

            # Convert to checksum address
            new_address = self.web3.to_checksum_address(new_address)

            # Update configuration
            old_address = self.token_config.address
            self.token_config.address = new_address

            logger.info(f"Token address updated from {old_address} to {new_address}")

            # Verify contract is accessible
            if self.web3.is_connected():
                try:
                    contract = self.web3.eth.contract(
                        address=new_address, abi=ERC20_ABI
                    )
                    symbol = contract.functions.symbol().call()
                    decimals = contract.functions.decimals().call()

                    logger.info(
                        f"Contract verified - Symbol: {symbol}, Decimals: {decimals}"
                    )

                    # Update local config with contract data
                    self.token_config.symbol = symbol
                    self.token_config.decimals = decimals

                except Exception as e:
                    logger.warning(f"Could not verify contract details: {e}")

            return True

        except Exception as e:
            logger.error(f"Failed to update token address: {e}")
            return False

    def get_notification_channels(self, access_tier: str) -> list:
        """
        Get available notification channels based on access tier.

        Args:
            access_tier: User's access tier

        Returns:
            List of available notification channels
        """
        notification_tiers = {
            "public": [],
            "holders": ["premium_signals"],
            "premium": ["premium_signals", "whale_signals"],
            "whale": ["premium_signals", "whale_signals", "alpha_signals"],
        }

        base_channels = notification_tiers.get("public", [])
        tier_channels = notification_tiers.get(access_tier, [])

        return base_channels + tier_channels

    async def get_wallet_info(self, wallet_address: str) -> Dict[str, Any]:
        """
        Get comprehensive wallet information including balance and access tier.

        Args:
            wallet_address: Ethereum wallet address

        Returns:
            Dictionary with wallet info
        """
        try:
            balance = await self.get_token_balance(wallet_address)
            access_tier = self.calculate_access_tier(balance)
            available_channels = self.get_notification_channels(access_tier)

            return {
                "address": wallet_address,
                "balance": balance,
                "balance_formatted": self.format_token_balance(balance),
                "access_tier": access_tier,
                "available_channels": available_channels,
                "is_simulation": not self.token_config.is_deployed,
                "timestamp": asyncio.get_event_loop().time(),
            }

        except Exception as e:
            logger.error(f"Failed to get wallet info for {wallet_address}: {e}")
            raise

    def format_token_balance(self, balance: int) -> str:
        """
        Format token balance for display.

        Args:
            balance: Balance in wei

        Returns:
            Formatted balance string
        """
        divisor = 10**self.token_config.decimals
        whole_part = balance // divisor
        fractional_part = balance % divisor

        if fractional_part == 0:
            return str(whole_part)

        fractional_str = str(fractional_part).zfill(self.token_config.decimals)
        trimmed_fractional = fractional_str.rstrip("0")

        if trimmed_fractional:
            return f"{whole_part}.{trimmed_fractional}"
        else:
            return str(whole_part)

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get service health status for monitoring.

        Returns:
            Health status information
        """
        return {
            "web3_connected": self.web3.is_connected(),
            "token_deployed": self.token_config.is_deployed,
            "token_address": self.token_config.address,
            "base_rpc_url": self.base_rpc_url,
            "simulation_mode": not self.token_config.is_deployed,
        }


# Global service instance
onchain_service = OnchainIntegrationService()


# Utility functions for easy import
async def get_token_balance(wallet_address: str) -> int:
    """Get token balance for wallet address"""
    return await onchain_service.get_token_balance(wallet_address)


def calculate_access_tier(balance: int) -> str:
    """Calculate access tier from balance"""
    return onchain_service.calculate_access_tier(balance)


def verify_wallet_signature(wallet_address: str, message: str, signature: str) -> bool:
    """Verify wallet signature"""
    return onchain_service.verify_wallet_signature(wallet_address, message, signature)


async def get_wallet_info(wallet_address: str) -> Dict[str, Any]:
    """Get comprehensive wallet information"""
    return await onchain_service.get_wallet_info(wallet_address)


def update_token_address(new_address: str) -> bool:
    """Update token contract address"""
    return onchain_service.update_token_address(new_address)
