-- ============================================================================
-- Triggers y procedimientos almacenados para taller_mecanico
-- Ejecutar SOLO las partes nuevas (NO re-importar script_mysql.sql completo
-- porque duplicaría los INSERT de usuarios).
-- Base: MariaDB 10.4 (XAMPP).
-- ============================================================================

USE taller_mecanico;

-- ---------------------------------------------------------------------------
-- Trigger: validar y descontar stock de refacciones al insertar un detalle
-- Dispara BEFORE INSERT en detalle_orden. Si es tipo 'refaccion', verifica
-- stock suficiente y lo decrementa. Si no hay stock, aborta con error
-- (la transacción del DAO hará rollback completo).
-- ---------------------------------------------------------------------------
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

-- ---------------------------------------------------------------------------
-- Trigger: restaurar stock al eliminar una línea de detalle (por DELETE CASCADE
-- de la orden o eliminación individual).
-- ---------------------------------------------------------------------------
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

-- ---------------------------------------------------------------------------
-- Procedimiento almacenado: sp_crear_orden
-- Carga la cabecera de una orden y devuelve el orden_id generado.
-- NOTA: no maneja COMMIT/ROLLBACK; el DAO controla la transacción completa
-- (cabecera + detalles) para garantizar atomicidad.
-- Parámetros:
--   p_matricula   VARCHAR(15)
--   p_cliente_id  INT UNSIGNED
--   p_usuario_id  INT UNSIGNED
-- Devuelve: p_orden_id (OUT) con el id de la orden creada.
-- ---------------------------------------------------------------------------
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