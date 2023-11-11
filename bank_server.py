#!/usr/bin/env python3
#
# Bank Server application
# Serena Geroe

import socket
import selectors

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


class CurrentState:
    """CurrentState instances keep track of details of the current state of the bank server machine"""
    # Class variables, whose vals get inherited by instances.
    logged_in = False
    accountNumber = 'zz-00000'
    sessionID = 0
    connection = "need to establish"
    address = "need to establish this too"

    # class variable, not instance --> does not vary across instances
    ACCTS_LOGGED_IN = dict() # dictionary containing the account numbers : sessionID of all accounts currently logged in.

    def __init__(self, logIn = False, actNum = "zz-00000", session_ID = 0, 
                 cn = "need to establish", ad = "need to establish this too"):
        """ Initialize the state variables of a new CurrentState instance. """
        self.logged_in = logIn
        self.accountNumber = actNum
        self.sessionID = session_ID
        self.connection = cn
        self.address = ad

    def logIn(self):
        self.logged_in = True
    
    def logout(self):
        self.logged_in = False

    def set_sessionID(self,ID):
        self.sessionID = ID

    def set_accountNum(self, ac):
        self.accountNumber = ac
    
    def set_connection(self, conn):
        self.connection = conn

    def set_address(self, addr):
        self.address = addr


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
        Success codes are: 0: valid result; 2: invalid amount given. """
        result_code = 0
        if not amountIsValid(amount):
            #result_code = 2
            return self, 2, self.acct_balance
        else:
            # valid amount, so add it to balance and set succes_code 1
            self.acct_balance += amount

        self.acct_balance = round(self.acct_balance,2)
        
        return self, result_code, self.acct_balance

    def withdraw(self, amount):
        """ Make a withdrawal. The value of amount must be valid for bank transactions. If amount is valid, update the acct_balance.
        This method returns three values: self, success_code, current balance.
        Success codes are: 0: valid result; 2: invalid amount given; 3: attempted overdraft. """
        result_code = 0
        if not amountIsValid(amount):
            # invalid amount, return error 
            # result_code = 2
            return self, 2, self.acct_balance
        elif amount > self.acct_balance:
            # attempted overdraft
            #result_code = 3
            return self, 3, self.acct_balance
        else:
            # all checks out, subtract amount from the balance
            self.acct_balance -= amount

            self.acct_balance = round(self.acct_balance,2)

        return self, result_code, self.acct_balance
    
    # validate pin inside the class
    def validatePin(self, otherPin):
        """Return true if a given pin matches the pin of this BankAccount."""
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
##########################################################

def validate_acct_pin_pair(client_msg, state: CurrentState):
    """ Validate the account number - pin pair based on the memory database.
    Returns the result code and this BankAccount object.
    Success code is: 0: valid result; 
    Error code is: 1: invalid account number - pin pair. """

    # server expecting a message of the form l,acct_num,pin

    go_ahead = False
    result_code = 5

    login_credentials_list = client_msg.split(",") #parse the client's message based on a comma delimeter
    account_string = login_credentials_list[1]
    this_acct = get_acct(account_string) # returns the BankAccount object being requested

    # check whether this account is logged in.
    # if this account is logged in, make sure it's in this session!
        # in this case, go_ahead = true  
    if this_acct.acct_number in CurrentState.ACCTS_LOGGED_IN:
        other_login_sessionID = CurrentState.ACCTS_LOGGED_IN.get(this_acct)

        if state.sessionID == other_login_sessionID:
            go_ahead = True

    elif go_ahead or account_string not in CurrentState.ACCTS_LOGGED_IN:

        if this_acct.validatePin(login_credentials_list[2]): #get_pin(login_credentials_list[1]):
            result_code = 0
            state.set_accountNum(login_credentials_list[1])
            state.logIn() # 
            CurrentState.ACCTS_LOGGED_IN.update({account_string:state.sessionID}) # this is how to access a class variable

        else: 
            result_code = 1
            emptyState = CurrentState()
            return result_code, emptyState #result_code = 1

    return result_code, state

# "Dispatch function"
def interpret_client_operation(msg, thisState:CurrentState):
    """Parses client request, sends client account balance, performs request.
    Result codes are: 0: valid result; 1: invalid login; 2: invalid amount; 3: attempted overdraft; 4: suspicious login""" 

    go_ahead = False

    op_list = msg.split(",") #op[0] = "l", "b", "d", or "w" | op[1] = param

    # DO NOT ASSUME THAT A RECEIVED MESSAGE WILL CONTAIN DATA IN THE EXPECTED FORMAT
    if (len(op_list) == 2 or len(op_list) == 3) and (all( isinstance( item, str ) for item in op_list) and (type(op_list[0]) == str) ):

        this_acct = get_acct(op_list[1])

        # Check whether this account is already logged in
        # this session ID is thisState.sessionID
        if this_acct.acct_number in CurrentState.ACCTS_LOGGED_IN:
            other_login_sessionID = CurrentState.ACCTS_LOGGED_IN.get(op_list[1])

            # if this account is already logged into THIS session (which IS valid), set go_ahead to True
            if thisState.sessionID == other_login_sessionID:
                go_ahead = True

        if go_ahead or this_acct.acct_number not in CurrentState.ACCTS_LOGGED_IN:

            # login
            if(op_list[0] == "l"):
                if(thisState.logged_in == False):
                    result_code, thisState =  validate_acct_pin_pair(msg, thisState) # check whether the acct_num - pin pair is valid
                else:
                    result_code = 4 #already logged in
                    return result_code, -1000       

            # balance check
            elif(op_list[0] == "b"):
                # no other steps needed. just communicate successful exchange of info between server and client
                # the server by default sends back the account balance
                # do not need to update the state
                result_code = 0      

            # deposit
            elif(op_list[0] == "d"):
                _, result_code, _ = this_acct.deposit(float(op_list[2]))

            # withdraw
            elif (op_list[0] == "w"):
                _, result_code, _ = this_acct.withdraw(float(op_list[2]))

            else:
                return 1, -1000 # nefarious client sending malformed request

            if result_code == 0: return result_code, get_balance(op_list[1])

            else: return result_code, get_balance(op_list[1])

        else: return 4, -1000 #result code is 1, report bal is -1000 since this is an invalid login!!

    else: return 4, -1000 #result code is 1, report bal is -1000 since this is an invalid login!!    

    
def accept_wrapper(sock, sel, seshID):
    """ Initiates the connection between the server and client, and sets the connection to be non-blocking.
    Takes as input parameters the socket object, the sel (selectors object), and the session ID.
    Returns this conn (connection object) and addr (address object)."""

    # Analogy: client knocks on the door. Server opens the door / initiates the connection
    # this is a NEW socket, different from the one the server is listening on
    # note: sock.accept() will NOT block
    # conn = connection object, addr is address of the connection
    conn, addr = sock.accept()  # Should be ready to read
    
    print(f"Accepted connection from {addr}\n")
    
    # ensures the conn object does not block
    conn.setblocking(False)

    # Instantiate a new CurrentState object, with the current session ID. set logged in to False.
    # do not set account number yet, since that will be taken care of in service_connection
    data_here = CurrentState(session_ID=seshID,logIn=False, cn = conn, ad = addr)

    #Don't worry about EVENT_WRITE part. 
    
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    
    # register this new connxn, the events of interest (EVENT_READ), and CurrentState
    sel.register(conn, events, data=data_here)

    return conn, addr


# Receives the data
def service_connection(sel, key, mask, conn, addr):
    """ Used when an existing connection is opened, this function
    receives the data from the client and listens for whether the client closed the connection.
    Takes as input the selector object, key, mask, connection object, and address for this connection."""    

   # Pulls out socket associated w the connxn
    sock = key.fileobj
    #Pulls out the data associated with this register, this instance of the CurrentState object
    data = key.data
    if mask & selectors.EVENT_READ:
   # receive the data from this register, in the form of a CurrentState object

        recv_data = sock.recv(1024)  # Should be ready to read
        # Note: DO NOT worry about the client sending too much data 
        print("Received client message: " + recv_data.decode('utf-8') + "\n")
        
        if not recv_data:
            #returns an empty bytes object, the server knows the client closed the connection
            print(f"Closing connection to session id {data.sessionID}\n")
            sel.unregister(sock)
            sock.close()
            data.logout()
            #remove this account number from the class variable
            if(len(CurrentState.ACCTS_LOGGED_IN) > 0):
                if data.accountNumber in CurrentState.ACCTS_LOGGED_IN and data.logged_in == True:
                    CurrentState.ACCTS_LOGGED_IN.pop(data.accountNumber)
            return

        # client_msg will be in string form because of the below line
        client_msg = recv_data.decode('utf-8')

        #note: data is type CurrentState
        run_bank_operations(conn, addr, client_msg, thisState=data)
 

def run_bank_operations(conn, addr, client_msg, thisState):
    """Sends server response to client based on client message."""
        
    print(f"Established connection, {addr}\n")

    # send message to client in the form of resultcode,balance    
    result_code, bal = interpret_client_operation(client_msg, thisState )

    response = str(result_code) + "," + str(bal)

    print("Sending client response: " + response + "\n")
    conn.sendall( response.encode('utf-8') )


def run_network_server():
    """ Runs the communication between the server and the client. """

    sessionID = 0

    print("Establishing connection to client - listening for connections at IP", HOST, "and port", PORT, " \n")
     
    sel = selectors.DefaultSelector()
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: #creates socket object with address family AF_INET and socket type SOCK_STREAM
        s.bind((HOST, PORT)) # associates the socket with the particular desired network interface and port number
        s.listen() # enables the server to accept connections; also accounts for the server's backlogged connections (ones that haven't yet been accepted)
       
        # from one-off: conn, addr = s.accept() # accept() blocks execution and waits for an incoming connection
        
        print(f"Listening on,{(HOST, PORT)}\n")

        s.setblocking(False) # configures the open socket in non-blocking mode
        
        # registers nonblocking open socket w selector object
        # the listening socket will generate a new event when a new connection is ready
        sel.register(s,selectors.EVENT_READ,data=None) #registers the socket to be monitored with sel.select()

        try:
            while True:
                # events is a list of tuples, one per socket
                # each tuple consists of a key (a SelectorKey namedtuple) and a mask
                # see more details at https://realpython.com/python-sockets/#handling-multiple-connections
                
                # below line is configured by sel.register line above 
                events = sel.select(timeout=None) #blocks until there are sockets ready for I/O, i.e. have events ready to be processed
                for key, mask in events:
                    #listening socket, need to accept the connection (i.e. new incoming client connxn, ready to be accepted)
                    if key.data is None: #returns third argument of object passed into sel.reg (data)
                    #    conn, addr = accept_wrapper(key.fileobj, sel, seshID=sessionID) #accepts the new incoming connection
                        accept_wrapper(key.fileobj, sel, seshID=sessionID) #accepts the new incoming connection
                    #    print("after accept: " + str(conn) + "," + str(addr))
                    # client socket which has already been accepted and needs servicing
                    else: #for previously accepted connxn's, those key.data values are NOT none --> this connxn exists
                        service_connection(sel=sel, key=key, mask=mask, conn = key.data.connection, addr=key.data.address)
                        # print("after service: " + str(conn) + "," + str(addr))
                # increment session ID, which will be the next unused value of session ID
                sessionID = sessionID + 1

        except KeyboardInterrupt as e: # if user hits delete or CTRL+C
            print("Caught keyboard interrupt, exiting\n")
            print(f"{e}") # Print the error
        finally:
            sel.close()    

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
    """ This function loads all bank accounts and runs the main network server function. """
    # on startup, load all the accounts from the account file
    load_all_accounts(ACCT_FILE)
    # uncomment the next line in order to run a simple demo of the server in action
    # demo_bank_server()
    run_network_server()
    print("bank server exiting...\n")