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

Blocks are published on a Poisson distribution around every ```Expected Block Time``` seconds as someone finds a block with a SHA256 hash H such that H < ```Target``` = ```((2**256) -1) / Difficulty ```. The state of the blockchain is saved by dumping the entire serialized list of accounts, as well as current difficulty, target, and some others. Currently no network support.

## Progress

* [x] Private/Public keys.
* [x] Transaction signing.
* [x] Block mining.
* [x] Persistence after restart.
* [x] Proof of Work for block creation.
* [ ] Smart Contract support.
* [ ] Create socket communication between nodes & send transactions.
* [ ] Create a mempool for pending transactions.
* [ ] Look for a simple Turing Complete language to add.