from lxml import etree

class Parser():

    # CREDENTIAL_FIELDS = ["owner_urn", "expires", "X509IssuerName"]
    REQUEST_FIELDS = ["HTTP_USER_AGENT", "REMOTE_ADDR"]
    NS_SIGN = "http://www.w3.org/2000/09/xmldsig#"

    @staticmethod
    def parse(request):
        parser = Parser()
        ds = dict()
        try:
            if isinstance(request, str):
                data = etree.fromstring(request)
                credential = parser.get_credential(data)
                ds["credential"] = parser.parse_credential(credential)
            else:
                ds["request"] = parser.parse_request_http(request.environ)
        except:
            import traceback
            print traceback.print_exc()
        return ds

    @staticmethod
    def get_credential(xml):
        return xml.xpath("//signed-credential")[0]

    @staticmethod
    def get_credential_expires(xml):
        expires = xml.xpath("//expires")
        expires = expires[0].text
        return expires

    @staticmethod
    def get_credential_issuer_name(xml):
        issuer_name = xml.xpath("//ns:X509IssuerName",
                      namespaces={"ns": Parser.NS_SIGN})
        issuer_name = issuer_name[0].text
        issuer_name = issuer_name.replace("CN=", "")
        return issuer_name

    @staticmethod
    def get_credential_owner_urn(xml):
        owner_urn = xml.xpath("//owner_urn")
        owner_urn = owner_urn[0].text
        return owner_urn

    @staticmethod
    def parse_credential(xml):
        cred = dict()
        cred["expires"] = Parser.get_credential_expires(xml)
        cred["issuer_name"] = Parser.get_credential_issuer_name(xml)
        cred["owner_urn"] = Parser.get_credential_owner_urn(xml)
        return cred

    @staticmethod
    def parse_request_http(request):
        filter_fields = {}
        for field in Parser.REQUEST_FIELDS:
            try:
                # Avoid parenthesis when comparing (pypelib does not allow them)
                filter_fields[field] = request[field].split("(")[0].strip()
            except:
                import traceback
                print traceback.print_exc()
        return filter_fields
 
