# simplechain

Minimal, Proof-of-Work local blockchain implementation in Python, for fun. Ethereum-like and equiped with a Turing Complete smart contract language.

## Note
This implementation is, intentionally, based only on my own knowledge about cryptocurrencies plus some Ethereum Yellow Paper consulting. No tutorials or looking at other people's code. Not intended for production, but for my own enjoyment.

## Why Python 
Since I do not care about performance as this will not go to production, Python allows me to code faster and leaves more time to think about the architecture itself.

## How does it work
It follows an account model like Ethereum as opposed to Bitcoin and Cardano's UTXO. The classes below model the basic structure of the chain.
```
Account             Transaction         Block
| Private Key       | From              | Number
| Address*          | To                | Timestamp
| Nonce             | Amount            | Nonce
| Balance           | Nonce             | Prev_Hash
| Code**            | Signature         | Txs (list[Transaction])
| Storage**         | Data**
                    | Gas Price

                    Blockchain
                    | Difficulty
                    | Target
                    | Expected Block Time
                    | Blocks (list[Block])
                    | Accounts (list[Account])

* derived from Private Keys with SECP256k1 curves
** for smart contracts.
```

Blocks are published on a Poisson distribution around every ```Expected Block Time``` seconds as someone finds a block with a SHA256 hash H such that H < ```Target``` = ```((2**256) -1) / Difficulty ```. The state of the blockchain is saved by dumping the entire serialized list of accounts, as well as current difficulty, target, and some others.

Smart contracts are supported. Creation of smart contracts is done by sending a transaction to the zero address ```(0x0000000000000000000000000000000000000000)``` with a ```data``` dict containing a key ```code``` with value being a plain-text string of Python code (correct indentation necessary), as well as a key ```variables``` with a dict definition of all variables and its initial values. Later, the functions can be called with another transaction where ```data``` has a ```call``` key, with value being the function and arguments to be called.

Contracts addresses are calculated from the SHA256 hash of the deployer address concatenated with their nonce.

For example:

```python
    data = {"code": "def set_a(n):\n\tglobal a; a = increment(n)\ndef increment(x):\n\t return x + 1", "variables": {"a": 0}}
    data2 = {"call": "set_a(5)"}
    tx = a.send_transaction(
        to=ZERO_ADDRESS, amount=0, data=data
    )
    deploy_address = "0x" + hashlib.sha256((a.address + str(a.nonce)).encode()).hexdigest()[:40]
    tx2 = a.send_transaction(to=deploy_address, amount=0, data=data2) 
```

After mining the block, we see the output:

```
Creating contract at address 0xa3ce91ebce4327b0b32e35810cd62f910d76ff60
Executing code:
def set_a(n):
        global a; a = increment(n)
def increment(x):
         return x + 1
set_a(5)
Storage before: {'a': 0}
Storage after: {'a': 6}
```

In the current implementation, we just concatenate whatever the user passes as value of ```call``` to the contract code. This would allow ACE or Arbitrary Code Execution, but it's an easy fix. 
Currently no network support.

## Progress

* [x] Private/Public keys.
* [x] Transaction signing.
* [x] Block mining.
* [x] Persistence after restart.
* [x] Proof of Work for block creation.
* [X] Turing Complete Smart Contract support.
* [ ] Create an ERC-20 clone and Uniswap clones.
* [ ] Create socket communication between nodes & send transactions.
* [ ] Create a mempool for pending transactions.