# Identity and access management (IAM)

IAM is the part of rastro that knows who a person is and how that person proves it.

## Language

**Identity**:
A person known to rastro, identified by one email address.
_Avoid_: User, account, profile

**Credentials**:
The email address and password that a person presents to prove that they own an Identity.
_Avoid_: Login data, auth data

**Session**:
The period in which a client acts as one Identity, from the moment rastro accepts its Credentials until the Session ends.
_Avoid_: Login (as a noun), token
