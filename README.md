# merkle-airdrop-contract
Merkle airdrop contract is example of usage of simple and very efficient method for executing 
arbitrary action on very large set of Ethereum addresses.

## Overview
Contract allows to mint() fixed amount of tokens to very big amount of addresses, using Merkle proof, provided by user. User claims his
tokens by providing additional data in transaction. It allows to prepare a really big list of addresses, set amount of tokens to give, 
calculate merkle root (a single hash, that "contains" all hashes in binary tree) and deploy very lightweight and simple contract,
described below.

## Description
Example user story:

1. Owner of contract prepares a list of addresses with many entries and publishes this list in public static .js file in JSON format
2. Owner reads this list, builds the merkle tree structure and writes down the Merkle root of it.
3. Owner creates contract and places calculated Merkle root into it.
4. Owner says to users, that they can claim their tokens, if they owe any of addresses, presented in list, published on onwer's site.
5. User wants to claim his N tokens, he also builds Merkle tree from public list and prepares Merkle proof, consisting from log2N hashes, describing the way to reach Merkle root
6. User sends transaction with Merkle proof to contract
7. Contract checks Merkle proof, and, if proof is correct, then sender's address is in list of allowed addresses, and contract does some action for this use. In our case it mints some amount of token
  
## Notes 
Merkle tree data structure is the very efficient way to check if arbitrary data is in some list when we're not able to store this list in contract, it takes too much storage space. In our case we store a single hash in contract, allowing user to build the proof by himself. This scheme has advantage in sotrage requirements, but requires additional computations on client side, so, use in wisely.





