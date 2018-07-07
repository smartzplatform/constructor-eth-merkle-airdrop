'use strict';
import {sha3, bufferToHex} from 'ethereumjs-util';

import Web3 from 'web3'
const web3 = new Web3()

import assertBnEq from '../test/helpers/assertBigNumbersEqual';
import MerkleTree from '../test/helpers/merkleTree';
import expectThrow from '../test/helpers/expectThrow';

//const BigNumber = web3.BigNumber;
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
	const TOKENS_TO_TRANSFER = 1000; // new BigNumber(100);
	let mintableToken;
	let merkleAirdrop;

	// build merkle tree for allowed set of addresses
	const allowed_addresses_list = [roles.user1, roles.user2, roles.user3, roles.user4];
	const merkleTree = new MerkleTree(allowed_addresses_list);
   	const merkleRootHex = merkleTree.getHexRoot();

	// build merkle tree for not allowed set of addresses
	const not_allowed_addresses_list = [roles.nobody1, roles.nobody2, roles.nobody3, roles.nobody4];
	const merkleBadTree = new MerkleTree(not_allowed_addresses_list); // to make "fake" valid proof

	function generateLeafs(n) {
		let leafs = [];
		for(let i=0; i < n; i++) {
			let acc = web3.eth.accounts.create(""+i);
			leafs.push(acc.address);
		}
		return leafs;
	}

   it("generates file with many addresses for test", async function() {
   		return true;
        this.timeout(10000);                                                                                                                                             
                                                                                                                                                       
        const fs = require('fs');
                                                                                                                                                  
        let leafs = generateLeafs(500);
        let tree = new MerkleTree(leafs);                                                                                                                                
        let root = tree.getHexRoot();
		  let data = '0xc4F75d2D9D581D077CF04F056A99180445f52602'; // my addr
        leafs.forEach(leaf => data += "\n" + leaf);                                                                                        
        fs.writeFileSync(root + ".txt", data);                                                                                                                       
	
	});
	
	it("tests deployment of airdrop contract and updating its token balance", async function() {
		mintableToken = await MintableToken.new({from: roles.owner});
		merkleAirdrop = await MerkleAirdrop.new(mintableToken.address, merkleRootHex, TOKENS_TO_TRANSFER, {from: roles.owner});
		await mintableToken.mint(merkleAirdrop.address, TOTAL_TOKENS_FOR_AIRDROP, {from: roles.owner});
			
		const user1_proof = await merkleTree.getHexProof(roles.user1);
		const leaf = await '0x' + sha3(roles.user1).toString('hex');

      assert.isOk(await merkleAirdrop.checkProof(user1_proof, leaf), 'checkProof did not return true for a valid proof');
      assert.isNotOk(await merkleAirdrop.checkProof(user1_proof, merkleRootHex), 'checkProof did not return false for a non valid proof');
    });


	it("tests contract check proof function", async function() {
		const user1_proof = await merkleTree.getHexProof(roles.user1);

		const leaf = await '0x' + sha3(roles.user1).toString('hex');
      assert.isOk(await merkleAirdrop.checkProof(user1_proof, leaf), 'checkProof did not return true for a valid proof');
      assert.isNotOk(await merkleAirdrop.checkProof(user1_proof, merkleRootHex), 'checkProof did not return false for a non valid proof');
    });

    it("tests for success mint for allowed set of users", async function() {
		for(let i = 0; i <= allowed_addresses_list.length - 1; i++) {
			let check_addr = allowed_addresses_list[i];
			let merkle_proof = await merkleTree.getHexProof(check_addr);

			let airdropContractBalance = await mintableToken.balanceOf(merkleAirdrop.address);
			let userTokenBalance = await mintableToken.balanceOf(check_addr);

			let mintIsOk = await merkleAirdrop.mint_by_merkle_proof(merkle_proof, check_addr);
			assert.isOk(mintIsOk, 'mint_by_merkle_proof did not return true for a valid proof');

			assertBnEq(await mintableToken.balanceOf(merkleAirdrop.address), airdropContractBalance.minus(TOKENS_TO_TRANSFER), "balance of airdrop contract was not decreased by TOKENS_TO_TRANSFER");
			assertBnEq(await mintableToken.balanceOf(check_addr), userTokenBalance.plus(TOKENS_TO_TRANSFER), "balance of user was not increased by TOKENS_TO_TRANSFER");
		}
	});

   it("tests for failed mint for not allowed set of users", async function() {
		for(let i = 0; i <= not_allowed_addresses_list.length - 1; i++) {
			let check_addr = not_allowed_addresses_list[i];
			let merkle_proof = await merkleBadTree.getHexProof(check_addr);
			let leaf = await '0x' + sha3(check_addr).toString('hex');

			let startAirdropContractBalance = await mintableToken.balanceOf(merkleAirdrop.address)
			let startUserBalance = await mintableToken.balanceOf(check_addr);

			assert.isNotOk(await merkleAirdrop.checkProof(merkle_proof, leaf), 'checkProof did not return false for an invalid proof');
			assertBnEq(await mintableToken.balanceOf(check_addr), startUserBalance, "balance of user changed after not allowed user request");
			assertBnEq(await mintableToken.balanceOf(merkleAirdrop.address),  startAirdropContractBalance, "balance of airdrop contract changed after not allowed user request");
		}
	});


});
