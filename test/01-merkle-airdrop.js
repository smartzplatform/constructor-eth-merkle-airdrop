'use strict';
import {sha3, bufferToHex} from 'ethereumjs-util';

import Web3 from 'web3'
const web3 = new Web3()
const fs = require('fs');

import assertBnEq from '../test/helpers/assertBigNumbersEqual';
import MerkleTree from '../test/helpers/merkleTree';
import expectThrow from '../test/helpers/expectThrow';

const MerkleAirdrop = artifacts.require("MerkleAirdrop.sol");

const MintableToken = artifacts.require("openzeppelin-solidity/contracts/token/ERC20/MintableToken.sol");

const l = console.log;

contract('MerkleAirdrop', function(accs) {

    const roles =  {
        owner: accs[0],
		user1: accs[1],
		user2: accs[2],
		user3: accs[3],
		user4: accs[4],
        nobody1: accs[5],
        nobody2: accs[6],
        nobody3: accs[7],
        nobody4: accs[8],
        nobody5: accs[9],
	};


	// create token contract, mint some tokens and give them to airdrop contract
	const TOTAL_TOKENS_FOR_AIRDROP = 1000000;// new BigNumber(1000);
	const NUM_TOKENS_PER_USER = 10;
	let mintableToken;
	let merkleAirdrop;
	let leafsArray = [];
	let merkleTree;
	let merkleRootHex;

	function generateLeafs(n) {
		let leafs = [];
		for(let i=0; i < n; i++) {
			let acc = web3.eth.accounts.create(""+i);
			// lowercase is important!
			leafs.push('' + acc.address.toLowerCase() + ' ' + 100);
		}
		return leafs;
	}

	const CANCELABLE = false;

   it("generates many addresses(of file optionally) for test, reads them and builds merkleTree", async function() {
   		// return true;
        this.timeout(10000);

        leafsArray = generateLeafs(4);
		leafsArray.push(roles.user1 + ' 100');
		leafsArray.push(roles.user2 + ' 88');
		leafsArray.push(roles.user3 + ' 99');
		leafsArray.push(roles.user4 + ' 66');
        merkleTree = new MerkleTree(leafsArray);
        merkleRootHex = merkleTree.getHexRoot();

		// uncomment here to receive a file with addresses, similar to real file, provided by user
		// be careful with big list sizes, use concatenation to join them
        // let data = leafsArray.join("\n");
        // fs.writeFileSync(merkleRootHex, data);
	});

	it("tests deployment of airdrop contract and minting tokens for airdrop", async function() {
		// deploy token contract, then give many tokens to deployed airdrop contract.
		mintableToken = await MintableToken.new({from: roles.owner});
		merkleAirdrop = await MerkleAirdrop.new(mintableToken.address, merkleRootHex, CANCELABLE, {from: roles.owner});
		assert.equal(await merkleAirdrop.merkleRoot(), merkleTree.getHexRoot());

		await mintableToken.mint(merkleAirdrop.address, TOTAL_TOKENS_FOR_AIRDROP, {from: roles.owner});
		assert.equal(await merkleAirdrop.contractTokenBalance(), TOTAL_TOKENS_FOR_AIRDROP,);
    });

 	it("tests for success mint for allowed set of users", async function() {
		// check correctness of mint for each in leafsArray
		for(let i = 0; i < leafsArray.length; i++) {

			// string like "0x821aea9a577a9b44299b9c15c88cf3087f3b5544 99000000"
			let leaf = leafsArray[i];

			let merkle_proof = await merkleTree.getHexProof(leaf);
			
			// await l("For string '" + leaf + "', and leaf: '" + '0x' + sha3(leaf).toString('hex') + "' generated proof: " + JSON.stringify(merkle_proof) );
			let userAddress = leaf.split(" ")[0];
			let numTokens = leaf.split(" ")[1];

			let airdropContractBalance = await mintableToken.balanceOf(merkleAirdrop.address);
			let userTokenBalance = await mintableToken.balanceOf(userAddress);

			assert.isOk(await merkleAirdrop.getTokensByMerkleProof(merkle_proof, userAddress, numTokens), 'getTokensByMerkleProof() did not return true for a valid proof');

			assertBnEq(await mintableToken.balanceOf(merkleAirdrop.address), airdropContractBalance.minus(numTokens), "balance of airdrop contract was not decreased by numTokens");
			assertBnEq(await mintableToken.balanceOf(userAddress), userTokenBalance.plus(numTokens), "balance of user was not increased by numTokens");
		}
	});

 	it("tests for success mint for newly added users", async function() {
		leafsArray.push(roles.nobody1 + ' 31');
		leafsArray.push(roles.nobody2 + ' 32');
		leafsArray.push(roles.nobody3 + ' 33');
		leafsArray.push(roles.nobody4 + ' 34');

		merkleTree = new MerkleTree(leafsArray);
        merkleRootHex = merkleTree.getHexRoot();
      	await merkleAirdrop.setRoot(merkleRootHex);
		let newRoot = await merkleAirdrop.merkleRoot();
      	assert.equal(newRoot, merkleRootHex, "updated merkle root '" + merkleRootHex, "' was not set in contract");

		// check minting for new addresses (nobody1 and nobody2, added in previous test)

		let leaf = roles.nobody1 + ' 31';
		let merkle_proof = await merkleTree.getHexProof(leaf);
		// await l("For string '" + leaf + "', and leaf: '" + '0x' + sha3(leaf).toString('hex') + "' generated proof: " + JSON.stringify(merkle_proof) );
		let userAddress = leaf.split(" ")[0];
		let numTokens = leaf.split(" ")[1];

		let airdropContractBalance = await mintableToken.balanceOf(merkleAirdrop.address);
		let userTokenBalance = await mintableToken.balanceOf(userAddress);

		assert.isOk(await merkleAirdrop.getTokensByMerkleProof(merkle_proof, userAddress, numTokens), 'getTokensByMerkleProof() did not return true for a valid proof');
		assertBnEq(await mintableToken.balanceOf(merkleAirdrop.address), airdropContractBalance.minus(numTokens), "balance of airdrop contract was not decreased by numTokens");
		assertBnEq(await mintableToken.balanceOf(userAddress), userTokenBalance.plus(numTokens), "balance of user was not increased by numTokens");
    });

 	//if (CANCELABLE == true) {
	it("tests for claiming all tokens on contract's balance and selfdestruct", async function() {
	let startAirdropContractBalance = await mintableToken.balanceOf(merkleAirdrop.address)
	let startUserBalance = await mintableToken.balanceOf(roles.owner);

	await expectThrow(merkleAirdrop.claim_rest_of_tokens_and_selfdestruct({from: roles.user1}), 'claiming rest of tokens by not owner did not broke call');
	assert.isOk(await merkleAirdrop.claim_rest_of_tokens_and_selfdestruct({from: roles.owner}), 'claiming rest of tokens by owner did not return true');
	assertBnEq(await mintableToken.balanceOf(roles.owner), startUserBalance.plus(startAirdropContractBalance), "balance of owned was not increased after caliming all rest of tokens");
	assertBnEq(await mintableToken.balanceOf(merkleAirdrop.address), 0, "balance of contract after claiming tokens not zero");
	});
	//} else {
	it("test for tokens claiming method-call revert", async function () {
		await expectThrow(merkleAirdrop.claim_rest_of_tokens_and_selfdestruct({from: roles.owner}), 'claiming is forbidden in this contract');
	});
	//}
	// [FIXME] [FIXME] add more and more tests!!!

});
