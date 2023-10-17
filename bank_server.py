#!/usr/bin/env python3
#
# Bank Server application
# Serena Geroe

import socket

HOST = "127.0.0.1"      # Standard loopback interface address (localhost)
PORT = 65432            # Port to listen on (non-privileged ports are > 1023)
ALL_ACCOUNTS = dict()   # initialize an empty dictionary
ACCT_FILE = "accounts.txt"

##########################################################
#                                                        #
# Bank Server Core Functions                             #
#                                                        #
# No Changes Needed in This Section                      #
#                                                        #
##########################################################

def acctNumberIsValid(ac_num):
    """Return True if ac_num represents a valid account number. This does NOT test whether the account actually exists, only
    whether the value of ac_num is properly formatted to be used as an account number.  A valid account number must be a string,
    lenth = 8, and match the format AA-NNNNN where AA are two alphabetic characters and NNNNN are five numeric characters."""
    return isinstance(ac_num, str) and \
        len(ac_num) == 8 and \
        ac_num[2] == '-' and \
        ac_num[:2].isalpha() and \
        ac_num[3:8].isdigit()

def acctPinIsValid(pin):
    """Return True if pin represents a valid PIN number. A valid PIN number is a four-character string of only numeric characters."""
    return (isinstance(pin, str) and \
        len(pin) == 4 and \
        pin.isdigit())

def amountIsValid(amount):
    """Return True if amount represents a valid amount for banking transactions. For an amount to be valid it must be a positive float()
    value with at most two decimal places."""
    return isinstance(amount, float) and (round(amount, 2) == amount) and (amount >= 0)

# TODO update this
class CurrentState:
    """CurrentState instances keep track of details of the current state of the bank server machine"""
    logged_in = False
    acccountNumber = 'zz-00000'
    sessionID = 0

    def __init__(self, logIn = False, actNum = "zz-00000", session_ID = 0):
        """ Initialize the state variables of a new CurrentState instance. """
        self.logged_in = logIn
        self.acccountNumber = actNum
        self.sessionID = session_ID

    def logIn(self):
        self.logged_in = True
    
    def logout(self):
        self.logged_in = False

    def set_sessionID(self,ID):
        self.sessionID = ID

    def set_accountNum(self, ac):
        self.acccountNumber = ac

class BankAccount:
    """BankAccount instances are used to encapsulate various details about individual bank accounts."""
    acct_number = ''        # a unique account number
    acct_pin = ''           # a four-digit PIN code represented as a string
    acct_balance = 0.0      # a float value of no more than two decimal places
    
    def __init__(self, ac_num = "zz-00000", ac_pin = "0000", bal = 0.0):
        """ Initialize the state variables of a new BankAccount instance. """
        if acctNumberIsValid(ac_num):
            self.acct_number = ac_num
        if acctPinIsValid(ac_pin):
            self.acct_pin = ac_pin
        if amountIsValid(bal):
            self.acct_balance = bal

    def deposit(self, amount):
        """ Make a deposit. The value of amount must be valid for bank transactions. If amount is valid, update the acct_balance.
        This method returns three values: self, success_code, current balance.
        Success codes are: 0: valid result; 1: invalid amount given. """
        result_code = 0
        if not amountIsValid(amount):
            result_code = 1
        else:
            # valid amount, so add it to balance and set succes_code 1
            self.acct_balance += amount

        self.acct_balance = round(self.acct_balance,2)
        
        return self, result_code, self.acct_balance

    def withdraw(self, amount):
        """ Make a withdrawal. The value of amount must be valid for bank transactions. If amount is valid, update the acct_balance.
        This method returns three values: self, success_code, current balance.
        Success codes are: 0: valid result; 1: invalid amount given; 2: attempted overdraft. """
        result_code = 0
        if not amountIsValid(amount):
            # invalid amount, return error 
            result_code = 1
        elif amount > self.acct_balance:
            # attempted overdraft
            result_code = 2
        else:
            # all checks out, subtract amount from the balance
            self.acct_balance -= amount

            self.acct_balance = round(self.acct_balance,2)

        return self, result_code, self.acct_balance
    
    # validate pin inside the class
    def validatePin(self, otherPin):
        return self.acct_pin == otherPin

def get_acct(acct_num):
    """ Lookup acct_num in the ALL_ACCOUNTS database and return the account object if it's found.
        Return False if the acct_num is invalid. """
    if acctNumberIsValid(acct_num) and (acct_num in ALL_ACCOUNTS):
        return ALL_ACCOUNTS[acct_num] 
    else:
        return False
    
def get_balance(acct_num):
    """Returns this account's balance"""
    return get_acct(acct_num).acct_balance

def load_account(num_str, pin_str, bal_str):
    """ Load a presumably new account into the in-memory database. All supplied arguments are expected to be strings. """
    try:
        # it is possible that bal_str does not represent a float, so be sure to catch that error.
        bal = float(bal_str)
        if acctNumberIsValid(num_str):
            if get_acct(num_str):
                print(f"Duplicate account detected: {num_str} - ignored")
                return False
            # We have a valid new account number not previously loaded
            new_acct = BankAccount(num_str, pin_str, bal)
            # Add the new account instance to the in-memory database
            ALL_ACCOUNTS[num_str] = new_acct
            print(f"loaded account '{num_str}'")
            return True
    except ValueError:
        print(f"error loading acct '{num_str}': balance value not a float")
    return False
    
def load_all_accounts(acct_file = "accounts.txt"):
    """ Load all accounts into the in-memory database, reading from a file in the same directory as the server application. """
    print(f"loading account data from file: {acct_file}")
    with open(acct_file, "r") as f:
        while True:
            line = f.readline()
            if not line:
                # we're done
                break
            if line[0] == "#":
                # comment line, no error, ignore
                continue
            # convert all alpha characters to lowercase and remove whitespace, then split on comma
            acct_data = line.lower().replace(" ", "").split(',')
            if len(acct_data) != 3:
                print(f"ERROR: invalid entry in account file: '{line}' - IGNORED")
                continue
            load_account(acct_data[0], acct_data[1], acct_data[2])
    print("finished loading account data")
    return True

##########################################################
#                                                        #
# Bank Server Network Operations                         #
#                                                        #
# TODO: THIS SECTION NEEDS TO BE WRITTEN!!               #
#                                                        #
##########################################################

def validate_acct_pin_pair(client_msg, state: CurrentState):
    """ Validate the account number - pin pair based on the memory database.
    Returns the result code and this BankAccount object.
    Success code is: 0: valid result; 
    Error code is: 1: invalid account number - pin pair. """

    # server expecting a message of the form l,acct_num,pin

    login_credentials_list = client_msg.split(",") #parse the client's message based on a comma delimeter

    this_acct = get_acct(login_credentials_list[1]) # returns the BankAccount object being requested
    if this_acct.validatePin(login_credentials_list[2]): #get_pin(login_credentials_list[1]):
        result_code = 0
        state.set_accountNum(login_credentials_list[1])
        state.logIn()

    else: result_code = 1

    return result_code, state

def interpret_client_operation(msg, thisState:CurrentState):
    """Parses client request, sends client account balance, performs request.
    Success codes are: 0: valid result; 1: invalid amount given. """
    # TODO 1. Validate operation format, 2. Send appropriate and specific responses to client...
    
    result_code = 5
    cur_state = thisState

    op_list = msg.split(",") #op[0] = "l", "b", "d", or "w" | op[1] = param1, op[2] = param2
    
    this_acct = get_acct(op_list[1])

    # login
    if(op_list[0] == "l"):
        result_code, cur_state =  validate_acct_pin_pair(msg, thisState) # check whether the acct_num - pin pair is valid

    # balance check
    if(op_list[0] == "b"):
        # no other steps needed. just communicate successful exchange of info between server and client
        # the server by default sends back the account balance
        # do not need to update the state
        result_code = 0

    # deposit
    if(op_list[0] == "d"):
        _, result_code, _ = this_acct.deposit(float(op_list[2]))

    # withdraw
    if(op_list[0] == "w"):
        _, result_code, _ = this_acct.withdraw(float(op_list[2]))


    #TODO else:
    
    return result_code, cur_state, get_balance(op_list[1])

def run_network_server():
    """ Runs the communication between the server and the client. """

    sessionID = 0

    # Enable just one connection w ATM client ########################################################################
    print("Establishing connection to client - listening for connections at IP", HOST, "and port", PORT, " \n")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: #creates socket object with address family AF_INET and socket type SOCK_STREAM
        s.bind((HOST, PORT)) # associates the socket with the particular desired network interface and port number
        s.listen() # enables the server to accept connections; also accounts for the server's backlogged connections (ones that haven't yet been accepted)
        conn, addr = s.accept() # accept() blocks execution and waits for an incoming connection

        with conn: # once a connection is made with the client, a new socket object is returned from accept() (different socket from the listening socket)

            sessionID = sessionID + 1 # set session ID

            print(f"Established connection, {addr}\n")

            thisState = CurrentState(session_ID=sessionID)

            while True: # infinite while loop to loop over blocking calls to conn.recv()
                
                # receive client message
                client_msg = conn.recv(1024)
                print("Received client message: " + client_msg.decode('utf-8'))
                
                # if conn.recv() returns an empty bytes object, the server knows the client closed the connection
                if not client_msg:
                    break 
                
                # send message to client in the form of resultcode,balance
                result_code, current_state, bal = interpret_client_operation( client_msg.decode('utf-8') , thisState )
                response = str(result_code) + "," + str(bal)
                print("Sending client response: " + response)
                conn.sendall( response.encode('utf-8') )

                thisState = current_state
    
    thisState.logout()

    return # break out of the loop when the client terminates the session
   

##########################################################
#                                                        #
# Bank Server Demonstration                              #
#                                                        #
# Demonstrate basic server functions.                    #
# No changes needed in this section.                     #
#                                                        #
##########################################################

def demo_bank_server():
    """ A function that exercises basic server functions and prints out the results. """
    # get the demo account from the database
    acct = get_acct("zz-99999")
    print(f"Test account '{acct.acct_number}' has PIN {acct.acct_pin}")
    print(f"Current account balance: {acct.acct_balance}")
    print(f"Attempting to deposit 123.45...")
    _, code, new_balance = acct.deposit(123.45)
    if not code:
        print(f"Successful deposit, new balance: {new_balance}")
    else:
        print(f"Deposit failed!")
    print(f"Attempting to withdraw 123.45 (same as last deposit)...")
    _, code, new_balance = acct.withdraw(123.45)
    if not code:
        print(f"Successful withdrawal, new balance: {new_balance}")
    else:
        print("Withdrawal failed!")
    print(f"Attempting to deposit 123.4567...")
    _, code, new_balance = acct.deposit(123.4567)
    if not code:
        print(f"Successful deposit (oops), new balance: {new_balance}")
    else:
        print(f"Deposit failed as expected, code {code}") 
    print(f"Attempting to withdraw 12345.45 (too much!)...")
    _, code, new_balance = acct.withdraw(12345.45)
    if not code:
        print(f"Successful withdrawal (oops), new balance: {new_balance}")
    else:
        print(f"Withdrawal failed as expected, code {code}")
    print("End of demo!")

##########################################################
#                                                        #
# Bank Server Startup Operations                         #
#                                                        #
# No changes needed in this section.                     #
#                                                        #
##########################################################

if __name__ == "__main__":
    # on startup, load all the accounts from the account file
    load_all_accounts(ACCT_FILE)
    # uncomment the next line in order to run a simple demo of the server in action
    #demo_bank_server()
    run_network_server()
    print("bank server exiting...")
