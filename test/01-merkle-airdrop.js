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
	const NUM_TOKENS_PER_USER = 100;
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
			leafs.push('' + acc.address.toLowerCase() + ' ' + NUM_TOKENS_PER_USER);
		}
		return leafs;
	}

   it("generates many addresses(of file optionally) for test reads them and builds merkleTree", async function() {
   		// return true;
        this.timeout(10000);                                                                                                                                             
                                                                                                                                                       
        leafsArray = generateLeafs(20);
		leafsArray.push(roles.user1 + ' 100');
		leafsArray.push(roles.user2 + ' 88');
		leafsArray.push(roles.user3 + ' 99');
		leafsArray.push(roles.user4 + ' 66');
        merkleTree = new MerkleTree(leafsArray);                                                                                                                                
        merkleRootHex = merkleTree.getHexRoot();

		//let data = '';
        //leafs.forEach(leaf => data += "\n" + leaf);                                                                                        
        //fs.writeFileSync(root + ".txt", data);

	});

	it("tests deployment of airdrop contract and check the pure checkProof function", async function() {
		mintableToken = await MintableToken.new({from: roles.owner});
		merkleAirdrop = await MerkleAirdrop.new(mintableToken.address, merkleRootHex, {from: roles.owner});
		await mintableToken.mint(merkleAirdrop.address, TOTAL_TOKENS_FOR_AIRDROP, {from: roles.owner});
			
		const user1_proof = await merkleTree.getHexProof(leafsArray[0]);
		const leaf = await '0x' + sha3(leafsArray[0]).toString('hex');

      	assert.isOk(await merkleAirdrop.checkProof(user1_proof, leaf), 'checkProof did not return true for a valid proof');
      	assert.isNotOk(await merkleAirdrop.checkProof(user1_proof, merkleRootHex), 'checkProof did not return false for a non valid proof');
    });

 	it("tests for success mint for allowed set of users", async function() {
		for(let i = 0; i < leafsArray.length; i++) {
			
			let leaf = leafsArray[i];
			let merkle_proof = await merkleTree.getHexProof(leaf);

			let userAddress = leaf.split(" ")[0];
			let numTokens = leaf.split(" ")[1];

			let airdropContractBalance = await mintableToken.balanceOf(merkleAirdrop.address);
			let userTokenBalance = await mintableToken.balanceOf(userAddress);

			assert.isOk(await merkleAirdrop.mintByMerkleProof(merkle_proof, userAddress, numTokens), 'mintByMerkleProof() did not return true for a valid proof');

			assertBnEq(await mintableToken.balanceOf(merkleAirdrop.address), airdropContractBalance.minus(numTokens), "balance of airdrop contract was not decreased by numTokens");
			assertBnEq(await mintableToken.balanceOf(userAddress), userTokenBalance.plus(numTokens), "balance of user was not increased by numTokens");
		}
	});

	it("tests setting of merkle root", async function() {
		leafsArray.push(roles.nobody1 + ' 33');
        merkleTree = new MerkleTree(leafsArray);                                                                                                                                
        merkleRootHex = merkleTree.getHexRoot();
      	await merkleAirdrop.setRoot(merkleRootHex);
		let newRoot = await merkleAirdrop.merkleRoot();
      	assert.equal(newRoot, merkleRootHex, 'updated merkle root was not set');
    });


   	it("tests for claiming all tokens on contract's balance and selfdestruct", async function() {
		let startAirdropContractBalance = await mintableToken.balanceOf(merkleAirdrop.address)
		let startUserBalance = await mintableToken.balanceOf(roles.owner);

		await expectThrow(merkleAirdrop.claim_rest_of_tokens_and_selfdestruct({from: roles.user1}), 'claiming rest of tokens by not owner did not broke call');
		assert.isOk(await merkleAirdrop.claim_rest_of_tokens_and_selfdestruct({from: roles.owner}), 'claiming rest of tokens by owner did not return true');
		assertBnEq(await mintableToken.balanceOf(roles.owner), startUserBalance.plus(startAirdropContractBalance), "balance of owned was not increased after caliming all rest of tokens");
		assertBnEq(await mintableToken.balanceOf(merkleAirdrop.address), 0, "balance of contract after claiming tokens not zero");
	});


	// [FIXME] [FIXME] add more and more tests!!!

});
