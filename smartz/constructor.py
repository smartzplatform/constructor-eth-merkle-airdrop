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
                "tokenAddress", "merkleRoot"
            ],
            "additionalProperties": False,

            "properties": {
                "tokenAddress": {
                    "title": "Token address",
                    "description": "Address of ERC20 token contract to be distributed. Remember to send tokens to your new airdrop contract when it's deployed.",
                    "$ref": "#/definitions/address"
                },
                "merkleRoot": {
                    "title": "Airdrop whitelist",
                    "description": "Upload .txt file with your Airdrop participant list. File format is <address> <amount in Wei> (one address per line). BE AWARE that addresses should be in lower case and amout of tokens should be in Wei (smallest quant of your token). File will be automatically converted into Merkle Tree format and uploaded to IPFS. Merkle root will be saved to contract, but your should keep IPFS address and provide it to your airdrop users. Example whitelist file:\nhttps://ipfs.io/ipfs/QmcnbeYUmYfRreMuoQSR6R4FpjV155rrjatJ2XQMg5H26u/airdrop_list.txt\n",
                    "$ref": "#/definitions/hash"
                },
                "cancelable": {
                    "type": "boolean",
                    "default": True,
                    "title": "Airdrop cancellation flag",
                    "description": "This is a flag that makes possible for a contract owner to claim the rest of tokens and destruct it"
                }
            }
        }

        ui_schema = {
            "merkleRoot": {
                "ui:widget": "merkleRoot",
                "ui:options": {
                    "blockchain": "ethereum",
                }
            }
        }

        return {
            "result": "success",
            "schema": json_schema,
            "ui_schema": ui_schema
        }

    def construct(self, fields):

        cancelable_str = 'true' if fields['cancelable'] else 'false'

        source = self.__class__._TEMPLATE \
            .replace('%token_address%', fields['tokenAddress']) \
            .replace('%merkle_root%', fields['merkleRoot']) \
            .replace('%cancelable%', cancelable_str)

        return {
            "result": "success",
            'source': source,
            'contract_name': "MerkleAirdrop"
        }

    def post_construct(self, fields, abi_array):

        function_titles = {
            'merkleRoot': {
                'title': 'Merkle root',
                'description': 'Merkle-tree root of airdrop whitelist. Can be hard to be built by browser(processing possibly a big file), so have a patience.',
                'sorting_order': 20,
            },

            'tokenContract': {
                'title': 'Token contract',
                'description': 'Address of airdrop token contract, this token is being distributed. Airdrop contract must have non-zero balance of tokens to distribute them',
                'sorting_order': 10,
            },

            'contractTokenBalance': {
                'title': 'Airdrop token balance',
                'description': 'This amount tokens is now waiting on airdrop contract to be claimed.',
                'sorting_order': 30,
            },

            'cancelable': {
                'title': 'Cancellation availability',
                'description': 'Flag which defines whether airdrop can be cancelled',
                'sorting_order': 40,
            },

            'claim_rest_of_tokens_and_selfdestruct': {
                'title': 'Cancel airdrop',
                'description': 'Owner only function, which sends rest of tokens to owner and destroys airdrop contract.',
                'icon': {
                    'pack': 'materialdesignicons',
                    'name': 'close-outline'
                },
                'sorting_order': 130,
            },

            'getTokensByMerkleProof': {
                'title': 'Claim my tokens',
                'sorting_order': 110,
                'description': 'Claim tokens from Airdrop contract if your address is in the whitelist.',
                'inputs': [{
                    'title': 'IPFS path to file with addresses whitelist',
                    'ui:widget': 'merkleProof',
                    'ui:options': {
                        'blockchain': 'ethereum',
                        'addressInputPosition': 1,
                        'tokensInputPosition': 2,
                    }
                },{
                    'title': 'Requesting address',
                },{
                    'title': 'Requesting tokens amount',
                }],
                'icon': {
                    'pack': 'materialdesignicons',
                    'name': 'arrow-down-thick'
                }
            },

            'setRoot': {
                'title': 'Update airdrop whitelist',
                'sorting_order': 120,
                'description': 'If you want to change your Airdrop participant list in any way, upload full new list here.',
                'inputs': [{
                    'title': 'Merkle root',
                    'description': 'Upload .txt file with your Airdrop participant list. File format is <address> <amount in Wei> (one address per line). BE AWARE that addresses should be in lower case and amout of tokens should be in Wei (smallest quant of your token). File will be automatically converted into Merkle Tree format and uploaded to IPFS. Merkle root will be saved to contract, but your should keep IPFS address and provide it to your airdrop users. Example whitelist file:  https://ipfs.io/ipfs/QmcnbeYUmYfRreMuoQSR6R4FpjV155rrjatJ2XQMg5H26u/airdrop_list.txt)',
                    'ui:widget': 'merkleRoot',
                    "ui:options": {
                        "blockchain": "ethereum",
                    }
                }],
                'icon': {
                    'pack': 'materialdesignicons',
                    'name': 'briefcase-upload'
                }
            }
        }

        return {
            "result": "success",
            'function_specs': function_titles,
            'dashboard_functions': ['tokenContract', 'contractTokenBalance', 'cancelable']
        }


    # language=Solidity
    _TEMPLATE = """
pragma solidity ^0.4.20;

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
  function Ownable() public {
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
    OwnershipRenounced(owner);
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
    OwnershipTransferred(owner, _newOwner);
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
    Transfer(msg.sender, _to, _value);
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
    Transfer(_from, _to, _value);
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
    Approval(msg.sender, _spender, _value);
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
    Approval(msg.sender, _spender, allowed[msg.sender][_spender]);
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
    Approval(msg.sender, _spender, allowed[msg.sender][_spender]);
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
    Mint(_to, _amount);
  }
}


contract MerkleAirdrop {

    address owner;
    bytes32 public merkleRoot;
    bool public cancelable;
    // address of contract, having "transfer" function
    // airdrop contract must have ENOUGH TOKENS in its balance to perform transfer
    MintableToken public tokenContract;

    // fix already minted addresses
    mapping (address => bool) spent;
    event AirdropTransfer(address addr, uint256 num);
    
    modifier isCancelable() {
        require(cancelable, "forbidden action");
        _;
    }

    function MerkleAirdrop() public payable {
        owner = msg.sender;
        tokenContract = MintableToken(%token_address%);
        merkleRoot = %merkle_root%;
        cancelable = %cancelable%;
        
        %payment_code%
    }
    
    function setRoot(bytes32 _merkleRoot) public {
        require(msg.sender == owner);
        merkleRoot = _merkleRoot;
    }

    function contractTokenBalance() public view returns(uint) {
        return tokenContract.balanceOf(address(this));
    }

    function claim_rest_of_tokens_and_selfdestruct() public isCancelable returns(bool) {
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


    function getTokensByMerkleProof(bytes32[] _proof, address _who, uint256 _amount) public returns(bool) {
        require(spent[_who] != true);
        require(_amount > 0);
        // require(msg.sender = _who); // makes not possible to mint tokens for somebody, uncomment for more strict version

        if (!checkProof(_proof, leaf_from_address_and_num_tokens(_who, _amount))) {
            return false;
        }

        spent[_who] = true;

        if (tokenContract.transfer(_who, _amount) == true) {
            AirdropTransfer(_who, _amount);
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
"""
