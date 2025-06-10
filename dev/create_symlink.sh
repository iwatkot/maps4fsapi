#!/bin/bash

current_dir="$PWD"
parent_dir=$(dirname "$PWD")

maps4fs_repo_dir="${parent_dir}/maps4fs_symlink"
# Skip cloning if the directory already exists
if [ -d "$maps4fs_repo_dir" ]; then
    echo "Directory $maps4fs_repo_dir already exists, skipping cloning."
else 
    echo "Directory $maps4fs_repo_dir does not exist, starting to clone the repo."
    mkdir -p "$maps4fs_repo_dir"
    cd "$maps4fs_repo_dir"
    git clone -b spl https://github.com/iwatkot/maps4fs.git
fi

cd "$current_dir"

if [ ! -d ".venv" ]; then
    echo "Error: .venv directory not found, please execute sh create_venv.sh first."
    exit 1
fi

site_packages_dir=$(find .venv/lib -type d -name "site-packages" -print -quit)

if [ -z "$site_packages_dir" ]; then
    echo "Error: site-packages directory not found."
    exit 1
else
    echo "Site-packages directory found: $site_packages_dir"
fi

if [ -d "${site_packages_dir}/maps4fs" ]; then
    rm -r "${site_packages_dir}/maps4fs"
fi

cd "$site_packages_dir"
ln -s "${maps4fs_repo_dir}/maps4fs/maps4fs" .
echo "Symlink created successfully."

echo "Access cloned repository with maps4fs here: $maps4fs_repo_dir"