# Authentication (auth)

Auth is the part of rastro that knows who a person is and how that person proves it.

## Language

**User**:
A person known to rastro, identified by one email address.
_Avoid_: Identity, account, profile

**Credentials**:
The email address and password that a person presents to prove that they own a User.
_Avoid_: Login data, auth data

**Session**:
The period in which a client acts as one User, from the moment rastro accepts its Credentials until the Session ends. A Session ends when the client ends it or when its lifetime runs out.
_Avoid_: Login (as a noun), token (the Session token only identifies a Session)

**Session token**:
The random secret that a client presents to act in its Session. Whoever holds it acts as the User of that Session.
_Avoid_: Session id, session key

# Security (security)

Security is the part of rastro that controls what another site can make a browser do with rastro: send a command, read a response, or show rastro in a frame. Auth, not Security, knows who a person is.
