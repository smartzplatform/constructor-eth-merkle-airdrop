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
    bytes32 public merkleRoot;
	// string public ipfsHash;

    // address of contract, having "transfer" function
    // airdrop contract must have ENOUGH TOKENS in its balance to perform transfer
    MintableToken tokenContract;

    // fix already minted addresses
    mapping (address => bool) spent;
    event AirdropTransfer(address addr, uint256 num);

    constructor(address _tokenContract, bytes32 _merkleRoot) public {
        owner = msg.sender;
        tokenContract = MintableToken(_tokenContract);
        merkleRoot = _merkleRoot;
    }


    function setRoot(bytes32 _merkleRoot) public {
        require(msg.sender == owner);
        merkleRoot = _merkleRoot;
    }

	function contractTokenBalance() public view returns(uint) {
		return tokenContract.balanceOf(address(this));
	}

    function claim_rest_of_tokens_and_selfdestruct() public returns(bool) {
        // only owner
        require(msg.sender == owner);
        require(tokenContract.balanceOf(address(this)) >= 0);
        require(tokenContract.transfer(owner, tokenContract.balanceOf(address(this))));
        selfdestruct(owner);
        return true;
    }

    function addressToAsciiString(address x) internal pure returns (string) {
        bytes memory s = new bytes(40);
        for (uint i = 0; i < 20; i++) {
            byte b = byte(uint8(uint(x) / (2**(8*(19 - i)))));
            byte hi = byte(uint8(b) / 16);
            byte lo = byte(uint8(b) - 16 * uint8(hi));
            s[2*i] = char(hi);
            s[2*i+1] = char(lo);
        }
        return string(s);
    }

    function char(byte b) internal pure returns (byte c) {
        if (b < 10) return byte(uint8(b) + 0x30);
        else return byte(uint8(b) + 0x57);
    }


    function uintToStr(uint i) internal pure returns (string){
        if (i == 0) return "0";
        uint j = i;
        uint length;
        while (j != 0){
            length++;
            j /= 10;
        }
        bytes memory bstr = new bytes(length);
        uint k = length - 1;
        while (i != 0){
            bstr[k--] = byte(48 + i % 10);
            i /= 10;
        }
        return string(bstr);
    }

    function leaf_from_address_and_num_tokens(address _a, uint256 _n) internal pure returns(bytes32 ) {
        string memory prefix = "0x";
        string memory space = " ";

        // file with addresses and tokens have this format: "0x123...DEF 999", where 999 - num tokens
        // function simply calculates hash of such a string, given the target adddres and num_tokens

        bytes memory _ba = bytes(prefix);
        bytes memory _bb = bytes(addressToAsciiString(_a));
        bytes memory _bc = bytes(space);
        bytes memory _bd = bytes(uintToStr(_n));
        string memory abcde = new string(_ba.length + _bb.length + _bc.length + _bd.length);
        bytes memory babcde = bytes(abcde);
        uint k = 0;
        for (uint i = 0; i < _ba.length; i++) babcde[k++] = _ba[i];
        for (i = 0; i < _bb.length; i++) babcde[k++] = _bb[i];
        for (i = 0; i < _bc.length; i++) babcde[k++] = _bc[i];
        for (i = 0; i < _bd.length; i++) babcde[k++] = _bd[i];

        return bytes32(keccak256(abcde));
    }


    function mintByMerkleProof(bytes32[] _proof, address _who, uint256 _amount) public returns(bool) {
        require(spent[_who] != true);
        require(_amount > 0);
        // require(msg.sender = _who); // makes not possible to mint tokens for somebody, uncomment for more strict version

        if (!checkProof(_proof, leaf_from_address_and_num_tokens(_who, _amount))) {
            return false;
        }

        spent[_who] = true;

        if (tokenContract.transfer(_who, _amount) == true) {
            emit AirdropTransfer(_who, _amount);
            return true;
        }
		// throw if transfer fails, no need to spend gaz
        require(false);
    }

    function checkProof(bytes32[] proof, bytes32 hash) view internal returns (bool) {
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

        return h == merkleRoot;
    }
}
