import accessible_output2.outputs.nvda
import accessible_output2.outputs.sapi5

class SistemaFala:

    def __init__(self):

        self.nvda = accessible_output2.outputs.nvda.NVDA()
        self.sapi = accessible_output2.outputs.sapi5.SAPI5()

    def falar(self, texto):

        try:

            if self.nvda.is_active():
                self.nvda.speak(texto)

            else:
                self.sapi.speak(texto)

        except:
            print(texto)