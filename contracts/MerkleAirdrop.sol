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

contract MerkleAirdrop {

	address owner;
	bytes32 merkle_root;
	// fix already minted addresses
	mapping (address => bool) spent;
	event Mint(address, uint256);
	uint256 tokensToMint = 100;

    constructor(bytes32 _merkle_root) public {
    	owner = msg.sender;
		merkle_root = _merkle_root; 
	}


	function mint_by_merkle_proof(bytes proof) public {
		require(spent[msg.sender] != true);
		if (checkProof(proof, merkle_root, bytes32(msg.sender))) {
			spent[msg.sender] = true;
			emit Mint(msg.sender, tokensToMint);
		}
	}

	function checkProof(bytes proof, bytes32 root, bytes32 hash) public pure returns (bool) {
	    bytes32 el;
    	bytes32 h = hash;

		for (uint256 i = 32; i <= proof.length; i += 32) {
			assembly {
				el := mload(add(proof, i))
			}

			if (h < el) {
				h = keccak256(h, el);
			} else {
				h = keccak256(el, h);
			}
		}

		return h == root;
	}
}
