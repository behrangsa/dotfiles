#!/usr/bin/env ruby

require 'fileutils'

# Install SSH Config
FileUtils.mkdir_p "#{ENV['HOME']}/.ssh", :verbose => true
FileUtils.ln_s    "#{ENV['HOME']}/dotfiles/ssh/config", "#{ENV['HOME']}/.ssh/config", :force => true, :verbose => true