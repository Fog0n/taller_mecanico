-- Script de creación de la base de datos "taller_mecanico"
-- Importar desde phpMyAdmin (pestaña "Importar") o pegar en la pestaña SQL.

CREATE DATABASE IF NOT EXISTS taller_mecanico CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE taller_mecanico;

-- ---------------------------------------------------------------------------
-- Tabla usuarios: cuentas con acceso al sistema.
-- perfiles previstos: 'admin', 'recepcion'
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    usuario_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nombre     VARCHAR(100)  NOT NULL,
    email      VARCHAR(150)  NOT NULL UNIQUE,
    username   VARCHAR(50)   NOT NULL UNIQUE,
    password   VARCHAR(255)  NOT NULL,  -- NOTA: texto plano solo para pruebas iniciales
    perfil     ENUM('admin', 'recepcion') NOT NULL DEFAULT 'recepcion',
    PRIMARY KEY (usuario_id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Tabla clientes: personas atendidas por el taller.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clientes (
    cliente_id   INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nombre       VARCHAR(150) NOT NULL,
    telefono     VARCHAR(20)  NOT NULL,
    email        VARCHAR(150) DEFAULT NULL,
    rfc          VARCHAR(13)  DEFAULT NULL,
    tipo_cliente ENUM('persona_fisica', 'empresa') NOT NULL DEFAULT 'persona_fisica',
    usuario_id   INT UNSIGNED DEFAULT NULL,  -- Cliente registrado con cuenta de usuario
    frecuente    TINYINT(1)   NOT NULL DEFAULT 0,  -- 1 = cliente frecuente (marca manual)
    PRIMARY KEY (cliente_id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios (usuario_id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Tabla vehiculos: vehículos de los clientes.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vehiculos (
    matricula  VARCHAR(15)  NOT NULL,
    modelo     VARCHAR(50)  NOT NULL,
    marca      VARCHAR(50)  NOT NULL,
    color      VARCHAR(30)  DEFAULT NULL,
    cliente_id INT UNSIGNED NOT NULL,
    PRIMARY KEY (matricula),
    FOREIGN KEY (cliente_id) REFERENCES clientes (cliente_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Tabla servicios: catálogo de mano de obra.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS servicios (
    servicio_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nombre      VARCHAR(100)       NOT NULL,
    precio      DECIMAL(10, 2)     NOT NULL,
    PRIMARY KEY (servicio_id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Tabla refacciones: catálogo de repuestos y su inventario.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS refacciones (
    refaccion_id INT UNSIGNED   NOT NULL AUTO_INCREMENT,
    nombre       VARCHAR(100)   NOT NULL,
    precio       DECIMAL(10, 2) NOT NULL,
    stock        INT            NOT NULL DEFAULT 0,
    PRIMARY KEY (refaccion_id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Tabla ordenes: órdenes de trabajo por vehículo.
-- estados previstos: 'abierta', 'en_proceso', 'terminada', 'entregada', 'pagada'
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ordenes (
    orden_id     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    matricula    VARCHAR(15)        NOT NULL,
    cliente_id   INT UNSIGNED       NOT NULL,
    usuario_id   INT UNSIGNED       NOT NULL,  -- Usuario que levanta la orden
    fecha_entrada DATE              NOT NULL,
    hora_entrada TIME              NOT NULL,
    fecha_salida DATE              DEFAULT NULL,
    hora_salida  TIME              DEFAULT NULL,
    estado       ENUM('abierta', 'en_proceso', 'terminada', 'entregada', 'pagada')
                 NOT NULL DEFAULT 'abierta',
    PRIMARY KEY (orden_id),
    FOREIGN KEY (matricula) REFERENCES vehiculos (matricula)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (cliente_id) REFERENCES clientes (cliente_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (usuario_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Tabla detalle_orden: servicios o refacciones incluidos en cada orden.
-- tipo: 'servicio' o 'refaccion' (indica cómo interpretar item_id)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS detalle_orden (
    detalle_id      INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    orden_id        INT UNSIGNED    NOT NULL,
    tipo            ENUM('servicio', 'refaccion') NOT NULL,
    item_id         INT UNSIGNED    NOT NULL,
    cantidad        INT             NOT NULL DEFAULT 1,
    precio_unitario DECIMAL(10, 2)  NOT NULL,
    subtotal        DECIMAL(10, 2)  NOT NULL,
    PRIMARY KEY (detalle_id),
    FOREIGN KEY (orden_id) REFERENCES ordenes (orden_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Tabla pagos: pagos registrados por cada orden.
-- metodos previstos: 'efectivo', 'tarjeta', 'transferencia'
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pagos (
    pago_id     INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    orden_id    INT UNSIGNED    NOT NULL,
    monto       DECIMAL(10, 2)  NOT NULL,
    fecha_pago  DATE            NOT NULL,
    metodo_pago ENUM('efectivo', 'tarjeta', 'transferencia') NOT NULL DEFAULT 'efectivo',
    usuario_id  INT UNSIGNED    NOT NULL,  -- Usuario que registra el pago
    PRIMARY KEY (pago_id),
    FOREIGN KEY (orden_id) REFERENCES ordenes (orden_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (usuario_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------------
-- Usuarios de prueba.
-- NOTA: passwords en texto plano solo para las primeras pruebas.
-- En una etapa posterior se debe hashear (por ejemplo, con bcrypt).
-- ---------------------------------------------------------------------------
INSERT INTO usuarios (nombre, email, username, password, perfil) VALUES
('Administrador', 'admin@taller.local', 'admin', 'admin123', 'admin'),
('Recepción', 'recepcion@taller.local', 'recepcion', 'recepc123', 'recepcion');

-- ============================================================================
-- Triggers y procedimientos almacenados (ver db/triggers_procedures.sql)
-- ============================================================================

-- Trigger: descontar stock de refacciones al insertar detalle (BEFORE INSERT)
DROP TRIGGER IF EXISTS trg_detalle_orden_descontar_stock;
DELIMITER //
CREATE TRIGGER trg_detalle_orden_descontar_stock
BEFORE INSERT ON detalle_orden
FOR EACH ROW
BEGIN
    IF NEW.tipo = 'refaccion' THEN
        IF (SELECT stock FROM refacciones WHERE refaccion_id = NEW.item_id) < NEW.cantidad THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Stock insuficiente de la refacción seleccionada.';
        ELSE
            UPDATE refacciones
               SET stock = stock - NEW.cantidad
             WHERE refaccion_id = NEW.item_id;
        END IF;
    END IF;
END;//
DELIMITER ;

-- Trigger: restaurar stock al eliminar detalle (AFTER DELETE)
DROP TRIGGER IF EXISTS trg_detalle_orden_restaurar_stock;
DELIMITER //
CREATE TRIGGER trg_detalle_orden_restaurar_stock
AFTER DELETE ON detalle_orden
FOR EACH ROW
BEGIN
    IF OLD.tipo = 'refaccion' THEN
        UPDATE refacciones
           SET stock = stock + OLD.cantidad
         WHERE refaccion_id = OLD.item_id;
    END IF;
END;//
DELIMITER ;

-- Procedimiento: crear cabecera de orden (devuelve orden_id)
DROP PROCEDURE IF EXISTS sp_crear_orden;
DELIMITER //
CREATE PROCEDURE sp_crear_orden(
    IN  p_matricula   VARCHAR(15),
    IN  p_cliente_id  INT UNSIGNED,
    IN  p_usuario_id  INT UNSIGNED,
    OUT p_orden_id    INT UNSIGNED
)
BEGIN
    INSERT INTO ordenes (matricula, cliente_id, usuario_id,
                         fecha_entrada, hora_entrada, estado)
    VALUES (p_matricula, p_cliente_id, p_usuario_id,
            CURDATE(), CURTIME(), 'abierta');
    SET p_orden_id = LAST_INSERT_ID();
END;//
DELIMITER ;
