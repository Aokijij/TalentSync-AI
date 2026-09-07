JOB_SECTORS = tuple(
    sorted(
        (
            "Alimentos y bebidas",
            "Tecnologia y software",
            "Analitica y ciencia de datos",
            "Inteligencia artificial",
            "Finanzas y banca",
            "Salud y bienestar",
            "Educacion",
            "Marketing y publicidad",
            "Ventas y comercio",
            "Recursos humanos",
            "Legal",
            "Logistica y transporte",
            "Manufactura",
            "Construccion e ingenieria",
            "Energia y servicios publicos",
            "Telecomunicaciones",
            "Turismo y hoteleria",
            "Retail y consumo masivo",
            "Medios y entretenimiento",
            "Agricultura y medio ambiente",
            "Sector publico y social",
        ),
        key=lambda item: item.casefold(),
    )
)
