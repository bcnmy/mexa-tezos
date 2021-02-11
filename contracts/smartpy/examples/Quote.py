import smartpy as sp

# Import from URL
# meta_tx_contract_url = "https://raw.githubusercontent.com/bcnmy/mexa-tezos/dev/contracts/smartpy/MetaTransaction.py"
# MetaTxnTemplate = sp.import_script_from_url(url=meta_tx_contract_url)

# Import from smartPy named contract
MetaTxnTemplate = sp.import_stored_contract(name="MetaTxnTemplate")


class Quote(sp.Contract):
    def __init__(self):
        self.init(
            quote="",
            owner=sp.address("tz123"),
            spSender=sp.address("tz123")
        )

    @sp.entry_point
    def set_quote(self, new_quote):
        self.data.quote = new_quote
        self.data.owner = self.data.spSender


@sp.add_test(name="MetaTransaction")
def test():
    alice = sp.test_account("Alice")
    bob = sp.test_account("Bob")

    chainId = sp.chain_id_cst("0x9caecab9")

    # Create test scenario
    scenario = sp.test_scenario()
    scenario.table_of_contents()

    # Display test accounts
    scenario.h1("Accounts")
    scenario.show([alice, bob])

    # Generate and register Quote meta transaction contract
    scenario.h1("Quote DApp using Native Meta Transaction")
    quote = Quote()
    scenario.register(quote, show=False)
    quote_with_meta_tx = MetaTxnTemplate.MetaTransaction(baseContract=quote)
    scenario += quote_with_meta_tx

    # Test Case - 1
    quote_value = "The biggest adventure you can ever take is to live the life of your dreams - Oprah"
    scenario.h3("Alice sends a set quote request on her own")
    scenario += quote_with_meta_tx.set_quote(
        params=quote_value,
        key=sp.none,
        sig=sp.none
    ).run(sender=alice, chain_id=chainId)
    scenario.verify_equal(quote_with_meta_tx.data.baseState.quote, quote_value)
    scenario.verify_equal(
        quote_with_meta_tx.data.baseState.owner, alice.address)

    # Test Case - 2
    quote_value = "Building a mission and building a business go hand in hand - Zuckerberg"
    paramHash = sp.blake2b(sp.pack(quote_value))
    data = sp.pack(sp.record(
        chain_id=chainId,
        contract_addr=quote_with_meta_tx.address,
        counter=0,
        param_hash=paramHash
    ))
    sig = sp.make_signature(alice.secret_key, data, message_format='Raw')

    scenario.h3("Bob sends a Quote on behalf of Alice")
    scenario += quote_with_meta_tx.set_quote(
        params=quote_value,
        key=sp.some(alice.public_key),
        sig=sp.some(sig)
    ).run(sender=bob, chain_id=chainId, now=sp.timestamp("15665656"))
    scenario.verify_equal(quote_with_meta_tx.data.baseState.quote, quote_value)
    scenario.verify_equal(
        quote_with_meta_tx.data.baseState.owner, alice.address)

    # Test Case - 3
    # replay attack
    scenario.h3(
        "Bob sends the Quote he sent previously on behalf of Alice, replay attack")
    scenario += quote_with_meta_tx.set_quote(
        params=quote_value,
        key=sp.some(alice.public_key),
        sig=sp.some(sig)
    ).run(sender=bob, chain_id=chainId, now=sp.timestamp("15665656"), valid=False)

    # Test Case - 4
    # pubkey mismatch
    quote_value = "Failure is simply the opportunity to begin again, this time more intelligently - Ford"
    paramHash = sp.blake2b(sp.pack(quote_value))
    data = sp.pack(sp.record(
        chain_id=chainId,
        contract_addr=quote_with_meta_tx.address,
        counter=1,
        param_hash=paramHash
    ))
    sig = sp.make_signature(alice.secret_key, data, message_format='Raw')

    scenario.h3("Alice signs an invalid quote request, pubKey mismatch")
    scenario += quote_with_meta_tx.set_quote(
        params=quote_value,
        key=sp.some(bob.public_key),
        sig=sp.some(sig)
    ).run(sender=bob, chain_id=chainId, now=sp.timestamp("15665656"), valid=False)

    # Test Case - 5
    # chainId mismatch
    quote_value = "He who is not everyday conquering some fear has not learned the secret of life - R W Emerson"
    paramHash = sp.blake2b(sp.pack(quote_value))
    data = sp.pack(sp.record(
        chain_id=1,
        contract_addr=quote_with_meta_tx.address,
        counter=1,
        param_hash=paramHash
    ))
    sig = sp.make_signature(alice.secret_key, data, message_format='Raw')

    scenario.h3("Alice signs a invalid quote request, chainId mismatch")
    scenario += quote_with_meta_tx.set_quote(
        params=quote_value,
        key=sp.some(alice.public_key),
        sig=sp.some(sig)
    ).run(sender=bob, chain_id=chainId, now=sp.timestamp("15665656"), valid=False)

    # Test Case - 6
    # counter mismatch
    quote_value = "An entrepreneur is someone who jumps off a cliff and builds a plane on the way down - R Hoffman"
    paramHash = sp.blake2b(sp.pack(quote_value))
    data = sp.pack(sp.record(
        chain_id=chainId,
        contract_addr=quote_with_meta_tx.address,
        counter=165675656,
        param_hash=paramHash
    ))
    sig = sp.make_signature(alice.secret_key, data, message_format='Raw')

    scenario.h3("Alice signs an invalid quote request, counter mismatch")
    scenario += quote_with_meta_tx.set_quote(
        params=quote_value,
        key=sp.some(alice.public_key),
        sig=sp.some(sig)
    ).run(sender=bob, chain_id=chainId, now=sp.timestamp("15665656"), valid=False)
