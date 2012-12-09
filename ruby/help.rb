#!/usr/bin/env ruby

shortcuts = {
  '^a' => 'Go to the beginning of line',
  '^e' => 'Go to end of line',
  '^k' => 'Delete everything to the right',
  '^u' => 'Delete everything to the left',
  '^w' => 'Delete previous word',
  'ESC-b' => 'Go back one word',
  'ESC-f' => 'Go forward one word'
}

puts "Command line shortcuts: \n"
shortcuts.each { |key, value|
  puts "#{key}: #{value}"
}