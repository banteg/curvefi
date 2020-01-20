import sys
import json
from dataclasses import dataclass
from web3.auto import w3
from web3.middleware import name_to_address_middleware
from web3.contract import Contract

SWAP_ADDRESS = '0xe5FdBab9Ad428bBB469Dee4CB6608C0a8895CbA5'
TOKEN_ADDRESS = '0xDBe281E17540Da5305Eb2AeFB8CeF70E6dB1A0A9'
ABI = json.load(open('curve.abi'))

w3.middleware_onion.add(name_to_address_middleware(w3))

swap = w3.eth.contract(SWAP_ADDRESS, abi=ABI['swap']).caller()
token = w3.eth.contract(TOKEN_ADDRESS, abi=ABI['erc20']).caller()


@dataclass
class Coin:
    coin: Contract
    underlying: Contract
    decimals: int
    reserve: float

    @classmethod
    def from_index(cls, i):
        coin = w3.eth.contract(swap.coins(i), abi=ABI['cerc20']).caller()
        underlying = w3.eth.contract(swap.underlying_coins(i), abi=ABI['erc20']).caller()
        decimals = underlying.decimals()
        reserve = swap.balances(i) / 1e18 * coin.exchangeRateCurrent() / 10 ** decimals
        return cls(coin=coin, underlying=underlying, decimals=decimals, reserve=reserve)


coins = [Coin.from_index(i) for i in range(2)]

print('Currency reserves:')
for coin in coins:
    print(f'{coin.underlying.symbol()}: {coin.reserve:,.2f}')

fee = swap.fee() / 1e10
admin_fee = swap.admin_fee() / 1e10
print(f'Fee: {fee:.3%}')
print(f'Admin fee: {admin_fee:.3%}')
print(f'Virtual price: {swap.get_virtual_price() / 1e18}')

# show LP stats if address is provided
if len(sys.argv) > 1:
    me = sys.argv[1]
    me = w3.toChecksumAddress(me) if w3.isAddress(me) else me
    print('\nMy share:')

    token_balance = token.balanceOf(me) / 1e18
    token_supply = token.totalSupply() / 1e18
    share = token_balance / token_supply
    print(f'{token.symbol()}: {token_balance:,.2f}')

    for coin in coins:
        print(f'{coin.underlying.symbol()}: {coin.reserve * share:,.2f}')
