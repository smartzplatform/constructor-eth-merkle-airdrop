import time

from smartz.api.constructor_engine import ConstructorInstance


class Constructor(ConstructorInstance):

    def get_version(self):
        return {
            "result": "success",
            "blockchain": "ethereum",
            "version": 1
        }

    def get_params(self):
        json_schema = {
            "type": "object",
            "required": [
                "tokenAddress", "merkleRoot", "numTokensToTransfer"
            ],
            "additionalProperties": False,

            "properties": {
                "tokenAddress": {
                    "title": "Token address",                                                                                                                    
                    "description": "Address of ERC20 token to be issued to requesting user",
                    "$ref": "#/definitions/address"                                                                                                              
                },
            "merkleRoot": {
                "description": "Just type text, hash (keccak256) of it will be sent",
                "$ref": "#/definitions/hash"
            },
            "numTokensToTransfer": {                                                                                                                                       
                    "title": "Tokens count to transfer",                                                                                                                     
                    "description": "Tokens count to issue each requesting account",
                    "type": "string",                                                                                                                            
                    "pattern": "^([1-9][0-9]{0,54}|[0-9]{1,55}\.[0-9]{0,17}[1-9])$"                                                                              
                }            
            }
        }

        ui_schema = {}

        return {
            "result": "success",
            "schema": json_schema,
            "ui_schema": ui_schema
        }

    def construct(self, fields):

        source = self.__class__._TEMPLATE \
            .replace('%token_address%', fields['tokenAddress']) \
            .replace('%merkle_root%', fields['merkleRoot']) \
            .replace('%num_tokens_to_transfer%', fields['numTokensToTransfer'])

        return {
            "result": "success",
            'source': source,
            'contract_name': "Merkle Airdrop"
        }

    def post_construct(self, fields, abi_array):

        function_titles = {
            'setroot': {
                'title': 'Set Merkle Root',
                'sorting_order': 10,
                'description': 'Set root of Merkle Tree',
                'inputs': [{
                    'title': 'Merkle root',
                }]
            },
            'mint': {
                'title': 'Mint Tokens',
                'sorting_order': 20,
                'description': 'Mint tokens',
                'inputs': [{
                    'title': 'Receipient address',
                },{
                    'title': 'Merkle proof',
                }]
            }
        }

        return {
            "result": "success",
            'function_specs': function_titles,
            'dashboard_functions': ['setroot', 'mint']
        }


    # language=Solidity
    _TEMPLATE = """
pragma solidity ^0.4.23;

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

    constructor() public {
        owner = msg.sender;
        num_tokens_to_transfer = %num_tokens_to_transfer%;
        token_contract = %token_address%;
        merkle_root = %num_tokens_to_transfer%;
        %payment_code%   
    }

    function mint_by_merkle_proof(bytes32[] proof, address who) public returns(bool) {
        require(spent[who] != true);
        
        if (!checkProof(proof, keccak256(who))) {
            return false;
        }

        require(token_contract.balanceOf(address(this)) >= num_tokens_to_transfer);

        spent[who] = true;

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
    """
