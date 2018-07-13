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
                    "default" : "0x996623f01f9e1d56db146942922a867727beb35c",
                    "$ref": "#/definitions/address"                                                                                                              
                },
                "merkleRoot": {
                    "description": "Just type text, hash (keccak256) of it will be sent",
                    "default": "0x364375476c3df5ae1914e143bacf08df1a792ff0e7e4e46f70a96c574479bdab",
                    "$ref": "#/definitions/hash"
                },
                "numTokensToTransfer": {                                                                                                                                       
                    "title": "Tokens count to transfer",                                                                                                                     
                    "description": "Tokens count to issue each requesting account",
                    "default": "1000",
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
            'contract_name': "MerkleAirdrop"
        }

    def post_construct(self, fields, abi_array):

        function_titles = {
            'mint_by_merkle_proof': {
                'title': 'Mint Tokens',
                'sorting_order': 20,
                'description': 'Mint tokens',
                'inputs': [{
                    'title': 'Receipient address',
                },{                                                                                                                                                      
                    'title': 'Merkle proof',                                                                                                                             
                    'ui:widget': 'merkleProof',                                                                                                                          
                    'ui:options': {                                                                                                                                      
                        'blockchain': 'eth',                                                                                                                             
                    }                                                                                                                                                    
                }]
            }
        }

        return {
            "result": "success",
            'function_specs': function_titles,
            'dashboard_functions': ['mint_by_merkle_proof']
        }


    # language=Solidity
    _TEMPLATE = """
pragma solidity ^0.4.23;

library SafeMath {                                                                                                            
  function mul(uint256 a, uint256 b) internal pure returns (uint256) {                                                        
    if (a == 0) {                                                                                                             
      return 0;                                                                                                               
    }                                                                                                                         
    uint256 c = a * b;                                                                                                        
    assert(c / a == b);                                                                                                       
    return c;                                                                                                                 
  }                                                                                                                           
                                                                                                                              
  function div(uint256 a, uint256 b) internal pure returns (uint256) {                                                        
    // assert(b > 0); // Solidity automatically throws when dividing by 0                                                     
    uint256 c = a / b;                                                                                                        
    // assert(a == b * c + a % b); // There is no case in which this doesn't hold                                             
    return c;                                                                                                                 
  }                                                                                                                           
                                                                                                                              
  function sub(uint256 a, uint256 b) internal pure returns (uint256) {                                                        
    assert(b <= a);                                                                                                           
    return a - b;                                                                                                             
  }                                                                                                                           
                                                                                                                              
  function add(uint256 a, uint256 b) internal pure returns (uint256) {                                                        
    uint256 c = a + b;                                                                                                        
    assert(c >= a);                                                                                                           
    return c;                                                                                                                 
  }                                                                                                                           
}                         

contract Ownable {
  address public owner;


  event OwnershipRenounced(address indexed previousOwner);
  event OwnershipTransferred(
    address indexed previousOwner,
    address indexed newOwner
  );


  /**
   * @dev The Ownable constructor sets the original `owner` of the contract to the sender
   * account.
   */
  constructor() public {
    owner = msg.sender;
  }

  /**
   * @dev Throws if called by any account other than the owner.
   */
  modifier onlyOwner() {
    require(msg.sender == owner);
    _;
  }

  /**
   * @dev Allows the current owner to relinquish control of the contract.
   * @notice Renouncing to ownership will leave the contract without an owner.
   * It will not be possible to call the functions with the `onlyOwner`
   * modifier anymore.
   */
  function renounceOwnership() public onlyOwner {
    emit OwnershipRenounced(owner);
    owner = address(0);
  }

  /**
   * @dev Allows the current owner to transfer control of the contract to a newOwner.
   * @param _newOwner The address to transfer ownership to.
   */
  function transferOwnership(address _newOwner) public onlyOwner {
    _transferOwnership(_newOwner);
  }

  /**
   * @dev Transfers control of the contract to a newOwner.
   * @param _newOwner The address to transfer ownership to.
   */
  function _transferOwnership(address _newOwner) internal {
    require(_newOwner != address(0));
    emit OwnershipTransferred(owner, _newOwner);
    owner = _newOwner;
  }
}

contract ERC20Basic {
  function totalSupply() public view returns (uint256);
  function balanceOf(address who) public view returns (uint256);
  function transfer(address to, uint256 value) public returns (bool);
  event Transfer(address indexed from, address indexed to, uint256 value);
}

contract ERC20 is ERC20Basic {
  function allowance(address owner, address spender)
    public view returns (uint256);

  function transferFrom(address from, address to, uint256 value)
    public returns (bool);

  function approve(address spender, uint256 value) public returns (bool);
  event Approval(
    address indexed owner,
    address indexed spender,
    uint256 value
  );
}

contract BasicToken is ERC20Basic {
  using SafeMath for uint256;

  mapping(address => uint256) balances;

  uint256 totalSupply_;

  /**
  * @dev Total number of tokens in existence
  */
  function totalSupply() public view returns (uint256) {
    return totalSupply_;
  }

  /**
  * @dev Transfer token for a specified address
  * @param _to The address to transfer to.
  * @param _value The amount to be transferred.
  */
  function transfer(address _to, uint256 _value) public returns (bool) {
    require(_to != address(0));
    require(_value <= balances[msg.sender]);

    balances[msg.sender] = balances[msg.sender].sub(_value);
    balances[_to] = balances[_to].add(_value);
    emit Transfer(msg.sender, _to, _value);
    return true;
  }

  /**
  * @dev Gets the balance of the specified address.
  * @param _owner The address to query the the balance of.
  * @return An uint256 representing the amount owned by the passed address.
  */
  function balanceOf(address _owner) public view returns (uint256) {
    return balances[_owner];
  }

}

contract StandardToken is ERC20, BasicToken {

  mapping (address => mapping (address => uint256)) internal allowed;


  /**
   * @dev Transfer tokens from one address to another
   * @param _from address The address which you want to send tokens from
   * @param _to address The address which you want to transfer to
   * @param _value uint256 the amount of tokens to be transferred
   */
  function transferFrom(
    address _from,
    address _to,
    uint256 _value
  )
    public
    returns (bool)
  {
    require(_to != address(0));
    require(_value <= balances[_from]);
    require(_value <= allowed[_from][msg.sender]);

    balances[_from] = balances[_from].sub(_value);
    balances[_to] = balances[_to].add(_value);
    allowed[_from][msg.sender] = allowed[_from][msg.sender].sub(_value);
    emit Transfer(_from, _to, _value);
    return true;
  }

  /**
   * @dev Approve the passed address to spend the specified amount of tokens on behalf of msg.sender.
   * Beware that changing an allowance with this method brings the risk that someone may use both the old
   * and the new allowance by unfortunate transaction ordering. One possible solution to mitigate this
   * race condition is to first reduce the spender's allowance to 0 and set the desired value afterwards:
   * https://github.com/ethereum/EIPs/issues/20#issuecomment-263524729
   * @param _spender The address which will spend the funds.
   * @param _value The amount of tokens to be spent.
   */
  function approve(address _spender, uint256 _value) public returns (bool) {
    allowed[msg.sender][_spender] = _value;
    emit Approval(msg.sender, _spender, _value);
    return true;
  }

  /**
   * @dev Function to check the amount of tokens that an owner allowed to a spender.
   * @param _owner address The address which owns the funds.
   * @param _spender address The address which will spend the funds.
   * @return A uint256 specifying the amount of tokens still available for the spender.
   */
  function allowance(
    address _owner,
    address _spender
   )
    public
    view
    returns (uint256)
  {
    return allowed[_owner][_spender];
  }

  /**
   * @dev Increase the amount of tokens that an owner allowed to a spender.
   * approve should be called when allowed[_spender] == 0. To increment
   * allowed value is better to use this function to avoid 2 calls (and wait until
   * the first transaction is mined)
   * From MonolithDAO Token.sol
   * @param _spender The address which will spend the funds.
   * @param _addedValue The amount of tokens to increase the allowance by.
   */
  function increaseApproval(
    address _spender,
    uint256 _addedValue
  )
    public
    returns (bool)
  {
    allowed[msg.sender][_spender] = (
      allowed[msg.sender][_spender].add(_addedValue));
    emit Approval(msg.sender, _spender, allowed[msg.sender][_spender]);
    return true;
  }

  /**
   * @dev Decrease the amount of tokens that an owner allowed to a spender.
   * approve should be called when allowed[_spender] == 0. To decrement
   * allowed value is better to use this function to avoid 2 calls (and wait until
   * the first transaction is mined)
   * From MonolithDAO Token.sol
   * @param _spender The address which will spend the funds.
   * @param _subtractedValue The amount of tokens to decrease the allowance by.
   */
  function decreaseApproval(
    address _spender,
    uint256 _subtractedValue
  )
    public
    returns (bool)
  {
    uint256 oldValue = allowed[msg.sender][_spender];
    if (_subtractedValue > oldValue) {
      allowed[msg.sender][_spender] = 0;
    } else {
      allowed[msg.sender][_spender] = oldValue.sub(_subtractedValue);
    }
    emit Approval(msg.sender, _spender, allowed[msg.sender][_spender]);
    return true;
  }

}

contract MintableToken is StandardToken, Ownable {
  event Mint(address indexed to, uint256 amount);
  event MintFinished();

  bool public mintingFinished = false;


  modifier canMint() {
    require(!mintingFinished);
    _;
  }

  modifier hasMintPermission() {
    require(msg.sender == owner);
    _;
  }

  /**
   * @dev Function to mint tokens
   * @param _to The address that will receive the minted tokens.
   * @param _amount The amount of tokens to mint.
   * @return A boolean that indicates if the operation was successful.
   */
  function mint(
    address _to,
    uint256 _amount
  )
    hasMintPermission
    canMint
    public
    returns (bool)
  {
    totalSupply_ = totalSupply_.add(_amount);
    balances[_to] = balances[_to].add(_amount);
    emit Mint(_to, _amount);
    emit Transfer(address(0), _to, _amount);
    return true;
  }

  /**
   * @dev Function to stop minting new tokens.
   * @return True if the operation was successful.
   */
  function finishMinting() onlyOwner canMint public returns (bool) {
    mintingFinished = true;
    emit MintFinished();
    return true;
  }
}

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
        merkle_root = %merkle_root%;
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
