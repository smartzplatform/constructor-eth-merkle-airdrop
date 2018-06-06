/**
 * Copyright (C) 2018  Smartz, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND (express or implied).
 */

pragma solidity ^0.4.18;

/**
 * @title MerkleAirdrop
 * Mints fixed amount of tokens to anybody, presented merkle proof for merkle root, placed in contract
 *
 * @author Boogerwooger <sergey.prilutskiy@smartz.io>
 */
import 'openzeppelin-solidity/contracts/token/ERC20/MintableToken.sol';

contract MerkleAirdrop {

	address owner;
	bytes32 merkle_root;
	// address of contrract, that can mint tokens 
	// it must allow our airdrop contract to do this
	address token_to_mint;
	uint256 public NUM_TOKENS_TO_MINT = 100;

	// fix already minted addresses
	mapping (address => bool) spent;
	event AirdropMint(address, uint256);

    constructor(address _token_to_mint, bytes32 _merkle_root) public {
    	owner = msg.sender;
		token_to_mint = _token_to_mint;
		merkle_root = _merkle_root;
	}

	function mint_by_merkle_proof(bytes32[] proof) public returns(bool) {
		require(spent[msg.sender] != true);
		if (checkProof(proof, bytes32(msg.sender))) {
			spent[msg.sender] = true;
			if (MintableToken(token_to_mint).mint(msg.sender, NUM_TOKENS_TO_MINT) == true) {
				emit AirdropMint(msg.sender, NUM_TOKENS_TO_MINT);
				return true;
			}
		}
		return false;
	}

	function checkProof(bytes32[] proof, bytes32 hash) view public returns (bool) {
	    bytes32 el;
    	bytes32 h = hash;

		for (uint i = 0; i <= proof.length - 1; i += 1) {
			el = proof[i];

			if (h < el) {
				h = keccak256(h, el);
			} else {
				h = keccak256(el, h);
			}
		}

		return h == merkle_root;
	}
}
