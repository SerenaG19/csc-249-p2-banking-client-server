# Project 2 TODO
# Author: Brendan
# Utilized for Project Organization by Serena Geroe

## General Project Requirements

- [ ] You MUST use the provided bank_server and atm_client programs as your starting point. You MUST NOT implement your own bank server and client from scratch.
- [ ] You MAY extend the core banking functionality in the bank_server and atm_client, but only to the degree needed to enable the two components to be able to interoperate.
- [ ] Your code MUST be readable, well organized, and demonstrate care and attention to computer programming best practices. The provided bank_server and atm_client provide good examples of such practices: classes and functions with easy-to-understand names are used extensively; functions are kept short (under 20 lines is ideal); functions are commented, and comments are inserted at key points within the function body.

## Bank Server Requirements

- [ ] MUST run in its own computing process (i.e., in a dedicated terminal window).
- [ ] MUST allow multiple simultaneous ATM client connections.
- [ ] MUST communicate with ATM clients exclusively by sending and receiving messages over the network using an application-layer message protocol of your own design.
- [ ] MUST allow multiple ATM clients to send messages to the server and receive timely responses from the server. One client should never be blocked until other client(s) have completed all their transactions.
- [ ] MUST validate an account's PIN code before allowing any other transactions to be performed on that account.
- [ ] MUST prevent more than one ATM client at a time from accessing a bank account and performing transactions on it.
- [ ] MUST transmit error results to the client using numeric codes rather than literal message strings.
- [ ] After a customer "logs in" to their account from an ATM client, the server MUST allow any number of transactions to be performed during that client banking session. During the session, access to the account from other ATM clients MUST be rejected.
- [ ] MUST prevent malicious client applications (i.e., other than the implemented atm_client application) from being able to send messages the the server which cause the server to crash, behave incorrectly, and/or provide unauthorized access to customer bank accounts.
- [ ] The bank_server MAY generate console output for tracing and debugging purposes.
- [ ] The bank_server MUST NOT assume that any customer has access to the server's console.

## ATM Server Requirements

- [ ] MUST run in its own computing process (i.e., in a dedicated terminal window).
- [ ] MUST obtain all needed user inputs through keyboard interaction.
- [ ] MUST connect to only one bank_server at a time.
- [ ] MUST communicate with the bank_server exclusively by sending and receiving messages over the network using an application-layer message protocol of your own design.
- [ ] MUST require each banking session to being with a customer "log in" step, where the customer provides an account number and PIN which are then validated by the bank_server.
- [ ] MUST NOT allow a customer to perform any banking transactions unless their account number and PIN are first validated by the bank_server.
- [ ] MUST allow a customer to perform any sequence of deposits, withdrawals, and balance checks after they have validated their account number and PIN.
- [ ] MUST NOT allow a customer to overdraw their bank account.

## Message Specification Requirements

- [ ] This document MUST include a written summary of the application-layer message protocol you developed for all communications between the client and the server.
- [ ] Message formats MUST be documented using Augmented Backus–Naur form (ABNF). See <https://en.wikipedia.org/wiki/Augmented_Backus%E2%80%93Naur_form> for details on ABNF.
- [ ] In addition to the ABNF specification, you MUST include some examples of each type of message you have defined.
- [ ] You MUST describe the component fields of each message, what constitutes allowed values for each field, and expected receiver actions in response to each message.
- [ ] You MUST include a brief description of how you solved the design problem of preventing bank account access from more than one atm_client at a time.

## Where I'm at right now
- [ ] Start with enabling a single connection between the bank server and the ATM client.
    - [ ] Begin with editing server code, use P1 as reference code.
    Why does the bank server say account-pin pair is invalid? --> Need to start by implementing login_to_server() in client server code.