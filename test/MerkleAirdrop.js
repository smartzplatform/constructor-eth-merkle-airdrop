'use strict';
import {sha3, bufferToHex} from 'ethereumjs-util';

import MerkleTree from '../test/helpers/merkleTree';
import expectThrow from '../test/helpers/expectThrow';

const MerkleAirdrop = artifacts.require("MerkleAirdrop.sol");
const l = console.log;

contract('MerkleAirdrop', function(accounts) {

    const roles =  {
        owner: accounts[0],
		user1: accounts[1],
		user2: accounts[2],
		user3: accounts[3],
        nobody1: accounts[4],
        nobody2: accounts[5],
        nobody3: accounts[6],
        nobody4: accounts[7],
        nobody5: accounts[8],
	};


    it("complex test", async function() {
		const addresses_list = [roles.user1, roles.user2, roles.user3, roles.nobody1, roles.nobody2, roles.nobody3];
		const merkleTree = new MerkleTree(addresses_list);
    	const merkleRoot = merkleTree.getHexRoot();
		await l(merkleRoot);
		const instance = await MerkleAirdrop.new(merkleRoot, {from: roles.owner});
			
		const user1_proof = await merkleTree.getHexProof(roles.user1);
      	await l(user1_proof);

		const leaf = await bufferToHex(sha3(roles.user1));
		await l(leaf);
		const result = await instance.checkProof(user1_proof, merkleRoot, leaf);
      	assert.isOk(result, 'checkProof did not return true for a valid proof');


        // await expectThrow(instance.swap({from: role.participant1}));

    });
});
