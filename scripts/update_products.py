from store.models import Product, ProductFeature

data = {
    7: {
        'desc': 'Ángulo de acero estructural de alta resistencia, ideal para la construcción de marcos, soportes, estanterías y estructuras metálicas en general. Ofrece excelente soldabilidad y durabilidad, adaptándose a múltiples aplicaciones industriales y civiles.',
        'features': {'Material': 'Acero ASTM A36', 'Longitud': '6 metros', 'Acabado': 'Negro / Galvanizado', 'Uso': 'Estructural y Herrería'}
    },
    8: {
        'desc': 'Barras cuadradas macizas de acero al carbono, perfectas para herrería, rejas, portones y proyectos de construcción que requieren alta resistencia y un acabado uniforme. Fáciles de cortar, perforar y soldar.',
        'features': {'Material': 'Acero SAE 1010 / 1020', 'Longitud': '6 metros', 'Perfil': 'Cuadrado macizo', 'Resistencia': 'Alta'}
    },
    9: {
        'desc': 'Flanches o bridas de acero diseñados para la unión segura de tuberías, válvulas y equipos en sistemas de fluidos. Fabricados bajo estrictas normas de tolerancia y resistencia a la presión, garantizan conexiones herméticas y seguras.',
        'features': {'Material': 'Acero al carbono', 'Tipo': 'Slip-on / Welding Neck', 'Presión': '150 - 300 lbs', 'Norma': 'ASME/ANSI B16.5'}
    },
    10: {
        'desc': 'Mallas de acero electrosoldado diseñadas para el refuerzo de concreto en losas, pavimentos, muros y cimentaciones. Proporcionan excelente adherencia, previenen fisuras en el concreto y reducen los tiempos de instalación.',
        'features': {'Material': 'Acero de alta resistencia', 'Presentación': 'Panel o Rollo', 'Uso': 'Refuerzo estructural', 'Ventaja': 'Rápida instalación'}
    },
    11: {
        'desc': 'Ladrillos refractarios de alta alúmina, diseñados para soportar temperaturas extremas y choques térmicos. Ideales para la construcción de hornos, chimeneas, calderas, asadores y revestimientos industriales que operan a fuego directo.',
        'features': {'Material': 'Alúmina y Sílice', 'Temperatura máxima': 'Hasta 1600°C', 'Uso': 'Industrial y Doméstico', 'Resistencia': 'Choque térmico'}
    },
    12: {
        'desc': 'Aislante térmico y acústico a base de lana mineral. Excelente resistencia al fuego y retención de calor. Utilizada extensamente en el aislamiento de tuberías industriales, calderas, techos y paredes secas para la conservación de energía.',
        'features': {'Material': 'Lana de roca mineral', 'Propiedades': 'Ignífugo / Acústico', 'Densidad': 'Alta densidad', 'Presentación': 'Manta o Panel'}
    },
    13: {
        'desc': 'Vigas estructurales con perfil doble T (IPE/IPN) que proporcionan una excelente relación resistencia-peso. Son los elementos esenciales para la construcción de techos de grandes luces, galpones industriales, puentes y edificios.',
        'features': {'Perfil': 'Doble T (IPE / IPN)', 'Material': 'Acero ASTM A36', 'Longitud': '6 a 12 metros', 'Aplicación': 'Carga estructural pesada'}
    },
    14: {
        'desc': 'Vigas tipo UPM de acero al carbono, utilizadas comúnmente en la fabricación de chasis, estructuras de soporte y guías. Su perfil en forma de U brinda gran estabilidad geométrica y resistencia a la flexión.',
        'features': {'Perfil': 'Canal U (UPN/UPM)', 'Material': 'Acero estructural', 'Longitud': '6 a 12 metros', 'Uso': 'Marcos y bases de maquinaria'}
    },
    15: {
        'desc': 'Tuberías de acero al carbono, diseñadas para la conducción segura de fluidos, gases y también para usos estructurales. Ofrecen una resistencia excepcional a la presión, los impactos mecánicos y el desgaste.',
        'features': {'Material': 'Acero al carbono', 'Tipo': 'Con costura / Sin costura', 'Norma': 'ASTM A53 / API 5L', 'Uso': 'Industrial y Construcción'}
    },
    16: {
        'desc': 'Cal hidratada de alta pureza especial para el sector construcción. Ideal para la preparación de morteros, mezclas de albañilería, frisos, estabilización de suelos y acabados finos en paredes.',
        'features': {'Peso': '20 kg', 'Tipo': 'Cal Hidratada', 'Uso': 'Morteros y frisos', 'Rendimiento': 'Alto'}
    },
    17: {
        'desc': 'Manto o membrana asfáltica impermeabilizante, recubierta con aluminio o gravilla, ideal para sellar de forma definitiva techos, terrazas y cubiertas. Protege eficazmente contra la lluvia, la humedad constante y la radiación UV.',
        'features': {'Material': 'Asfalto modificado', 'Acabado': 'Aluminio / Gravilla', 'Espesor': '3 a 4 mm', 'Uso': 'Impermeabilización'}
    },
    18: {
        'desc': 'Mortero especial altamente resistente a las temperaturas extremas, formulado específicamente para asentar y unir firmemente ladrillos refractarios en la construcción o reparación de hornos, chimeneas y equipos térmicos.',
        'features': {'Resistencia al calor': 'Hasta 1500°C', 'Presentación': 'Cuñete / Saco', 'Curado': 'Secado al aire', 'Aplicación': 'Juntas refractarias'}
    },
    19: {
        'desc': 'Rollo de alambre recocido o galvanizado para usos múltiples en el área de la construcción. Sumamente flexible pero resistente a la tracción, es el material perfecto para el amarre firme de cabillas y estructuras de acero.',
        'features': {'Material': 'Acero recocido suave', 'Presentación': 'Rollo', 'Uso principal': 'Amarre de cabillas', 'Flexibilidad': 'Alta'}
    },
    20: {
        'desc': 'Láminas de acero recubiertas de manera uniforme con una capa de zinc para brindar una protección superior y duradera contra la corrosión y el óxido. Utilizadas en techos, conductos de ventilación, carrocerías y herrería general.',
        'features': {'Material': 'Acero Galvanizado', 'Calibres': 'Variados', 'Uso': 'Ductería, techos, herrería', 'Protección': 'Anticorrosiva (Zinc)'}
    }
}

for pid, info in data.items():
    try:
        product = Product.objects.get(id=pid)
        product.description = info['desc']
        product.save()
        
        # Clear existing features
        ProductFeature.objects.filter(product=product).delete()
        
        # Add new features
        for key, value in info['features'].items():
            ProductFeature.objects.create(product=product, name=key, value=value)
            
        print(f"Updated {product.product_name}")
    except Product.DoesNotExist:
        print(f"Product ID {pid} not found.")
    except Exception as e:
        print(f"Error on ID {pid}: {e}")

print("Update completed.")
