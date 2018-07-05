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

pragma solidity ^0.4.23;

/**
 * @title MerkleAirdrop
 * Transfers fixed amount of tokens to anybody, presented merkle proof for merkle root, placed in contract
 *
 * @author Boogerwooger <sergey.prilutskiy@smartz.io>
 */
import 'openzeppelin-solidity/contracts/token/ERC20/MintableToken.sol';

contract MerkleAirdrop {

	address owner;
	bytes32 merkle_root;

	// address of contract, having "transfer" function 
	// airdrop contract must have ENOUGH TOKENS in its balance to perform transfer
	MintableToken token_contract;
	uint256 public num_tokens_to_transfer;

	// fix already minted addresses
	mapping (address => bool) spent;
	event AirdropTransfer(address addr, uint256 num);

   constructor(address _token_contract, bytes32 _merkle_root, uint256 _num_tokens_to_transfer) public {
    	owner = msg.sender;
		num_tokens_to_transfer = _num_tokens_to_transfer;
		token_contract = MintableToken(_token_contract);
		merkle_root = _merkle_root;
	}

	function mint_by_merkle_proof(bytes32[] proof, address who) public returns(bool) {
		require(spent[who] != true);
		
		if (!checkProof(proof, keccak256(who))) {
			return false;
		}

		spent[who] = true;

		// require(token_contract.balanceOf(address(this)) >= num_tokens_to_transfer);

		if (token_contract.transfer(who, num_tokens_to_transfer) == true) {
			emit AirdropTransfer(msg.sender, num_tokens_to_transfer);
			return true;
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
