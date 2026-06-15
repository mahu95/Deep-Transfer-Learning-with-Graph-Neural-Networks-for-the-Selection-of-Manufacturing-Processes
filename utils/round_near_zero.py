"""Tiny numerical helper for snapping near-zero floats to exactly zero."""


def round_near_zero(value, tolerance=1e-3):
    """Return 0.0 if ``value`` is within ``tolerance`` of zero, else ``value``.

    Used to clean up floating-point noise (e.g. bounding-box dimensions and
    face-centre coordinates) so that values that should be zero compare equal.
    """
    if abs(value) <= tolerance:
        return 0.0
    else:
        return value
