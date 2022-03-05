import unittest

import helpers.content as content


class TestContentFromUrl(unittest.TestCase):

    def _fetch_and_validate(self, url: str, expected_method: str):
        results = content.from_url(url)
        assert results['url'] == url
        assert len(results['text']) > content.MINIMUM_CONTENT_LENGTH
        assert results['extraction_method'] == expected_method
        return results

    def test_failing_url(self):
        url = "chrome://newtab/"
        try:
            self._fetch_and_validate(url, None)
        except Exception:
            # this is an image, so it should return nothing
            assert True

    def test_not_html(self):
        url = "https://s3.amazonaws.com/CFSV2/obituaries/photos/4736/635311/5fecf89b1a6fb.jpeg"
        try:
            self._fetch_and_validate(url, None)
        except RuntimeError:
            # this is an image, so it should return nothing
            assert True

    def test_lanacion(self):
        url = 'https://www.lanacion.com.ar/seguridad/cordoba-en-marzo-asesinaron-a-tres-mujeres-nid1884942/'
        results = self._fetch_and_validate(url, content.METHOD_BOILER_PIPE_3)
        assert "Cuando llegaron los agentes encontraron a la mujer en el dormitorio" in results['text']
        assert "2016-03-31" == results['publish_date']

    def test_cnn(self):
        url = "https://www.cnn.com/2021/04/30/politics/mcconnell-1619-project-education-secretary/index.html"
        results = self._fetch_and_validate(url, content.METHOD_READABILITY)
        assert "McConnell is calling on the education secretary to abandon the idea." in results['text']

    def test_from_url_informe_correintes(self):
        url = "http://www.informecorrientes.com/vernota.asp?id_noticia=44619"
        results = self._fetch_and_validate(url, content.METHOD_READABILITY)
        assert "En este sentido se trabaja en la construcción de sendos canales a cielo abierto" in results['text']

    def test_from_url_página_12(self):
        url = "https://www.pagina12.com.ar/338796-coronavirus-en-argentina-se-registraron-26-053-casos-y-561-m"
        results = self._fetch_and_validate(url, content.METHOD_TRIFILATURA)
        assert "Por otro lado, fueron realizados en el día 84.085 tests" in results['text']


'''
    # disabled because it doesn't seem to exist anymore
    def test_from_url_ahora_noticias(self):
        url = "https://www.ahoranoticias.com.uy/2021/03/son-falsas-las-afirmaciones-de-la-inmunologa-roxana-bruno-integrante-de-la-agrupacion-epidemiologos-argentinos/"
        results = self._fetch_and_validate(url, content.METHOD_READABILITY)
        assert "Sobre el final de la entrevista Bruno mencionó a distintas" in results['text']
'''

if __name__ == "__main__":
    unittest.main()
