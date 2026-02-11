class ImpuestoService:
    def calcular(self, total):
        return total * 0.19


class ImpuestoFactory:

    @staticmethod
    def get_service():
        return ImpuestoService()
