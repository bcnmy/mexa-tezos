import smartpy as sp

# NOTE about the `spSender` variable
# spSender - Provides information about the current execution context, including the
# sender of the transaction. While these are generally available via
# sp.sender, they should not be accessed in such a direct
# manner, since when dealing with meta-transactions the account sending and
# paying for execution may not be the actual sender (as far as an application
# is concerned).
class MetaTransaction(sp.Contract):
    def __init__(self, base_contract):
        self.base_contract = base_contract
        self.init(
            user_counter=sp.big_map(tkey=sp.TAddress, tvalue=sp.TNat),
            base_state=base_contract.data,
        )

    def get_counter(self, address):
        counter = sp.local("counter", 0)
        sp.if self.data.user_counter.contains(address):
            counter.value = self.data.user_counter[address]
        return counter.value

    def increment_counter(self, address):
        sp.if ~self.data.user_counter.contains(address):
            self.data.user_counter[address] = 0
        self.data.user_counter[address] += 1

    def get_address_from_pub_key(self, pub_key):
        return sp.to_address(sp.implicit_account(sp.hash_key(pub_key)))

    def check_meta_tx_validity(self, key, signature, param_hash):
        address = self.get_address_from_pub_key(key)
        counter = self.get_counter(address)
        data = sp.pack(
            sp.record(
                chain_id=sp.chain_id,
                contract_addr=sp.self_address,
                counter=counter,
                param_hash=param_hash
            )
        )
        sp.verify(
            sp.check_signature(key, signature, data),
            "MISSIGNED"
        )
        self.increment_counter(address)

    # Update the implementation of functions to add meta-tx support
    # Note: This fn. is invoked by smartpy only at compile time
    def buildExtraMessages(self):
        for (name, f) in self.base_contract.messages.items():
            def message(self, params):
                former_base_state = self.base_contract.data
                self.base_contract.data = self.data.base_state

                # Add sig and key, optional parameters
                sp.set_type(params.sig, sp.TOption(sp.TSignature))
                sig = params.sig.open_some()
                sp.set_type(params.pub_key, sp.TOption(sp.TKey))
                pub_key = params.pub_key.open_some()

                # Original params without pub_key, sig
                ep_params = params.params

                sp_sender = sp.local("sp_sender", sp.sender)

                # Check if sig, key is present;
                # If so, validate meta_tx
                sp.if params.pub_key.is_some() | params.sig.is_some():
                    sp_sender.value = self.get_address_from_pub_key(
                        pub_key)
                    param_hash = sp.blake2b(sp.pack(ep_params))
                    self.check_meta_tx_validity(pub_key, sig, param_hash)
                
                self.base_contract.sp_sender = sp_sender.value

                # Original fn implementation
                f.addedMessage.f(self.base_contract, ep_params)
                self.base_contract.data = former_base_state

            self.addMessage(sp.entry_point(message, name))
