'use strict';
import {sha3, bufferToHex} from 'ethereumjs-util';


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
        nobody1: accs[4],
        nobody2: accs[5],
        nobody3: accs[6],
        nobody4: accs[7],
        nobody5: accs[8],
	};


    it("complex test", async function() {
		const addresses_list = [roles.user1, roles.user2, roles.user3, roles.nobody1, roles.nobody2, roles.nobody3];


		const merkleTree = new MerkleTree(addresses_list);
    	const merkleRootHex = merkleTree.getHexRoot();

		const mintableToken = await MintableToken.new({from: roles.owner});
		const merkle_contract = await MerkleAirdrop.new(mintableToken.address, merkleRootHex, {from: roles.owner});
			
		const user1_proof = await merkleTree.getHexProof(roles.user1);

		const leaf = await '0x' + sha3(roles.user1).toString('hex');

      	assert.isOk(await merkle_contract.checkProof(user1_proof, leaf), 'checkProof did not return true for a valid proof');
      	assert.isNotOk(await merkle_contract.checkProof(user1_proof, merkleRootHex), 'checkProof did not return false for a non valid proof');

    });

    it("big drop test", async function() {
		const addresses_list_allowed = [];
		const addresses_list_not_allowed = [];

		let i = 0;
		while (i++ < 33) {
			let acc = '' + web3.personal.newAccount('' + i);
			if (i % 2 == 0) {
				addresses_list_allowed.push(acc);
			} else {
				addresses_list_not_allowed.push(acc);
			}
		}

		const merkleTree = new MerkleTree(addresses_list_allowed);
		const merkleRootHex = merkleTree.getHexRoot();
		const mintableToken = await MintableToken.new({from: roles.owner});
		const merkle_contract = await MerkleAirdrop.new(mintableToken.address, merkleRootHex, {from: roles.owner});


		// await l("Checking all valid addresses");
		for(let i = 0; i < addresses_list_allowed.length - 1; i++) {
			let check_addr = addresses_list_allowed[i];
			let merkle_proof = await merkleTree.getHexProof(check_addr);
			let leaf = await '0x' + sha3(check_addr).toString('hex');
      		assert.isOk(await merkle_contract.checkProof(merkle_proof, leaf), 'checkProof did not return true for a valid proof');
			// await l("Check of valid addr: " + leaf + ": OK");
		}

		const merkleBadTree = new MerkleTree(addresses_list_not_allowed); // to make "fake" valid proof
		// await l("Checking all invalid addresses");
		for(let i = 0; i < addresses_list_not_allowed.length - 1; i++) {
			let check_addr = addresses_list_not_allowed[i];
			let merkle_proof = await merkleBadTree.getHexProof(check_addr);
			let leaf = await '0x' + sha3(check_addr).toString('hex');
      		assert.isNotOk(await merkle_contract.checkProof(merkle_proof, leaf), 'checkProof did not return true for a valid proof');
			// await l("Check of invalid addr: " + leaf + ": OK");
		}

	});

  	it("merkle mint test", async function() {
		const addresses_list = [roles.user1, roles.user2, roles.user3, roles.nobody1, roles.nobody2, roles.nobody3];

		const merkleTree = new MerkleTree(addresses_list);
    	const merkleRootHex = merkleTree.getHexRoot();

		const mintableToken = await MintableToken.new({from: roles.owner});
		const merkle_contract = await MerkleAirdrop.new(mintableToken.address, merkleRootHex, {from: roles.owner});
			
		const user1_proof = await merkleTree.getHexProof(roles.user1);
		const leaf = await '0x' + sha3(roles.user1).toString('hex');
		
      	assert.isOk(await merkle_contract.mint_by_merkle_proof(user1_proof, {from: roles.user1}), 'mint_by_merkle_proof failed');
		l(await mintableToken.balanceOf(roles.user1));		

	});

});
