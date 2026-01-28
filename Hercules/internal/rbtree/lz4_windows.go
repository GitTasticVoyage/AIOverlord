//go:build windows
// +build windows

package rbtree

import (
	"encoding/binary"
)

// CompressUInt32Slice provides a no-op compression on Windows (returns uncompressed data).
// On non-Windows systems, uses native C-based LZ4 compression.
func CompressUInt32Slice(data []uint32) []byte {
	// Simple no-op: just convert to bytes without compression
	result := make([]byte, len(data)*4)
	for i, v := range data {
		binary.LittleEndian.PutUint32(result[i*4:], v)
	}
	return result
}

// DecompressUInt32Slice provides a no-op decompression on Windows.
// On non-Windows systems, uses native C-based LZ4 decompression.
func DecompressUInt32Slice(data []byte, result []uint32) {
	// Simple no-op: just convert back from bytes
	for i := range result {
		result[i] = binary.LittleEndian.Uint32(data[i*4:])
	}
}
