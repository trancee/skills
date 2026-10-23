//! Deliberately bad controls are compiled only by Miri and ignored by default.

#[cfg(test)]
mod tests {
    #[test]
    fn safe_raw_owner_roundtrip() {
        let raw = Box::into_raw(Box::new([3_u32, 5, 8]));
        // SAFETY: into_raw supplied this live, aligned allocation; ownership is reclaimed once.
        let mut owned = unsafe { Box::from_raw(raw) };
        owned[1] += 2;
        assert_eq!(*owned, [3, 7, 8]);
    }

    #[test]
    fn safe_wire_endianness() {
        let wire = [0x01, 0x23, 0x45, 0x67];
        assert_eq!(u32::from_be_bytes(wire), 0x0123_4567);
        assert_eq!(0x0123_4567_u32.to_be_bytes(), wire);
    }

    #[test]
    fn safe_empty_and_boundary_slices() {
        let values = [10_u8, 20, 30];
        let (left, right) = values.split_at(0);
        assert_eq!(left, &[]);
        assert_eq!(right, &[10, 20, 30]);
        let (left, right) = values.split_at(values.len());
        assert_eq!(left, &[10, 20, 30]);
        assert_eq!(right, &[]);
    }

    #[cfg(miri)]
    #[test]
    #[ignore = "intentional UB control; run only through the smoke helper"]
    fn bad_use_after_free() {
        let raw = Box::into_raw(Box::new(41_u64));
        // Deliberate bug: reclaim and free the allocation, then read through the stale pointer.
        unsafe {
            drop(Box::from_raw(raw));
            assert_eq!(raw.read(), 41);
        }
    }

    #[cfg(miri)]
    #[test]
    #[ignore = "intentional leak control; run only through the smoke helper"]
    fn bad_memory_leak() {
        // A leak is safe Rust, but Miri's additional leak policy rejects this execution.
        let _ = Box::into_raw(Box::new([7_u8; 16]));
    }
}
