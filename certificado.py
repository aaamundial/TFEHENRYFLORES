from cryptography import x509
from cryptography.hazmat.primitives.serialization import pkcs12

def check_certificate(p12_file_path, p12_password):
    with open(p12_file_path, 'rb') as p12_file:
        private_key, certificate, _ = pkcs12.load_key_and_certificates(
            p12_file.read(),
            p12_password.encode()
        )
    
    key_usage = certificate.extensions.get_extension_for_oid(x509.oid.ExtensionOID.KEY_USAGE)
    print("Key Usage:")
    print("Digital Signature:", key_usage.value.digital_signature)
    print("Content Commitment:", key_usage.value.content_commitment)
    print("Key Encipherment:", key_usage.value.key_encipherment)
    print("Data Encipherment:", key_usage.value.data_encipherment)
    print("Key Agreement:", key_usage.value.key_agreement)

# Uso:
check_certificate('firma_1718249749.p12', 'Mli09mli#')